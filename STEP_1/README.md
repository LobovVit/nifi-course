# NiFi PG→PG demo 

## Общая теория 

- Базовая сущность - FlowFile
- шаг обработки - Processor 
- Между processor’ами - connections
- переиспользуемые сервисы - Controller Service
- У processor’а обычно есть - relationships


## что в compose
- `pg_src` (Источник: Postgres): схема и таблицы созданы и заполнены демонстрационными данными.
- `pg_dst` (целевая база данных PostgreSQL): схема и таблицы созданы (одинаковая структура), данных нет.
- `data_gen`: one-shot service, который применяет DDL к базам данных
- `nifi`: Apache NiFi 1.28.1

## Ports
- pg_src: localhost:5433
- pg_dst: localhost:5434
- nifi:   http://localhost:8080 (admin / adminadminadmin)

## Запуск
```bash
docker compose up -d --build
docker compose logs -f data_gen
```

## что в базах (лучше подключиться dbeaver и посмотреть глазами)
Source:
```bash
psql "host=localhost port=5433 dbname=demo user=demo password=demo" -c "select count(*) from bra.doc_d_001;"
psql "host=localhost port=5433 dbname=demo user=demo password=demo" -c "select count(*) from bra.doc_links_001;"
```

Target (таблицы сужествуют , кол-во должно быть 0):
```bash
psql "host=localhost port=5434 dbname=demo user=demo password=demo" -c "select count(*) from bra.doc_d_001;"
psql "host=localhost port=5434 dbname=demo user=demo password=demo" -c "select count(*) from bra.doc_links_001;"
```

## Обнуление 
```bash
docker compose down -v
```

## DBCP_SOURCE - настройка 
- Type: DBCPConnectionPool
- Database Connection URL: `jdbc:postgresql://pg_src:5432/demo` / `jdbc:postgresql://pg_dst:5432/demo`
- Driver Class Name: `org.postgresql.Driver`
- Driver Location(s): `/opt/nifi/nifi-current/drivers/postgresql-42.7.9.jar`
- User: `demo`
- Password: `demo`
- Validation Query: `SELECT 1`

## Flow для справочников (полная копия)
**Задача:** перелить `bra.ref_tofk` целиком (без фильтра).

Процессоры:
1. QueryDatabaseTableRecord
    - DBCP: `DBCP_SOURCE`
    - SQL:
      ```sql
      select * from bra.ref_tofk
      ```
    - Fetch Size: 5000
    - Max Rows Per Flow File: 500
2. PutDatabaseRecord
    - DBCP: `DBCP_TARGET`
    - Table Name: `bra.ref_tofk`
    - Statement Type: `INSERT`
    - Record Reader: AvroReader (Controller Service)
3. LogAttribute (не обязательно)

## Flow для документов (с фильтром по дате `created_date >= 2025-01-01`)

## Базовый паттерн Flow (для каждой таблицы)
```
QueryDatabaseTableRecord
  → SplitRecord (1 запись = 1 FlowFile)
    → ExecuteScript (Groovy: сборка UPSERT SQL с приведением типов)
      → PutSQL (DBCP_TARGET)
```

### Процессоры:
#### QueryDatabaseTableRecord (чтение из source)
- Database Connection Pooling Service: `DBCP_SOURCE`
- Table Name: `bra.doc_d_001` (для валидации)
- Custom Query: 
```sql
select id,
       (extract(epoch from created_date)*1000)::bigint as created_date_ms,
       tofk, doc_type, status,
       payload::text as payload_json
from bra.doc_d_001
where created_date >= timestamp '2025-01-01 00:00:00'
order by created_date
```
- Record Writer: `AvroRecordSetWriter`
####  SplitRecord (нарезка по 1 записи)
- Record Reader: `AvroReader` (Use Embedded Avro Schema)
- Record Writer: `JsonRecordSetWriter`
- Records Per Split: `1`
####  ExecuteScript (Groovy: UPSERT SQL)
- Script Engine: `Groovy`
- Script Body:
```groovy
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import groovy.json.JsonSlurper

def ff = session.get()
if(!ff) return

try {
  def jsonText = ''
  ff = session.write(ff, { inStream, outStream ->
    jsonText = inStream.getText(StandardCharsets.UTF_8.name())
    outStream.write(jsonText.getBytes(StandardCharsets.UTF_8))
  } as StreamCallback)

  def obj = new JsonSlurper().parseText(jsonText)

  def id = obj.id?.toString()
  def createdMs = obj.created_date_ms
  def tofk = obj.tofk?.toString()
  def docType = obj.doc_type?.toString()
  def status = obj.status?.toString()
  def payloadJson = obj.payload_json?.toString()

  def payloadEsc = payloadJson.replace("'", "''")

  def sql = """
insert into bra.doc_d_001 (id, created_date, tofk, doc_type, status, payload)
values (
  '${id}',
  to_timestamp(${createdMs} / 1000.0),
  '${tofk}',
  '${docType}',
  '${status}',
  '${payloadEsc}'::jsonb
)
on conflict (id) do update set
  created_date = excluded.created_date,
  tofk        = excluded.tofk,
  doc_type    = excluded.doc_type,
  status      = excluded.status,
  payload     = excluded.payload
;
""".trim()

  ff = session.write(ff, { inStream, outStream ->
    outStream.write(sql.getBytes(StandardCharsets.UTF_8))
  } as StreamCallback)

  ff = session.putAttribute(ff, "mig.table", "bra.doc_d_001")
  ff = session.putAttribute(ff, "mig.id", id)

  session.transfer(ff, REL_SUCCESS)
} catch(Exception e) {
  log.error("Failed to build SQL", e)
  ff = session.putAttribute(ff, "mig.error", e.toString())
  session.transfer(ff, REL_FAILURE)
}
```
**Relationships:**
- success → PutSQL
- failure → LogAttribute / DLQ (не auto-terminate)

**Тюнинг:**
- Concurrent Tasks: 2

####  PutSQL (запись в target)
**Properties:**
- JDBC Connection Pool: `DBCP_TARGET`
- Batch Size: 500 (для ускорения)
- Support Fragmented Transactions: false

**Relationships:**
- success → auto-terminate
- failure → LogAttribute / DLQ
- retry → LogAttribute / DLQ

**Scheduling:**
- Concurrent Tasks: 2

## Производительность (быстрое ускорение)
- PutSQL: Batch Size = 500–1000, Concurrent Tasks = 2–4
- ExecuteScript: Concurrent Tasks = 2
- Если нужно быстрее — перейти на пакетную генерацию SQL (multi-row INSERT)