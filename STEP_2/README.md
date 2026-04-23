# NiFi PG→PG demo 

## что в compose
- `pg_src` (Источник: Postgres): схема и таблицы созданы и заполнены демонстрационными данными.
- `pg_dst` (целевая база данных PostgreSQL): схема и таблицы созданы (одинаковая структура), данных нет.
- `data_gen`: one-shot service, который применяет DDL к базам данных
- `nifi`: Apache NiFi 1.28.1
- `nifi_registry`:  Registry: 1.28.0

## Ports
- pg_src: localhost:5433
- pg_dst: localhost:5434
- nifi:   http://localhost:8080 (admin / adminadminadmin)
- nifi_registry: http://localhost:18080/nifi-registry/

## Запуск
```bash
docker compose up -d --build
```

## что в базах
Source:
```
подключиться dbeaver и посмотреть
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
## Создание Bucket + Добавление Registry Client 

Name: rms-demo
URL: http://nifi-registry:18080

## Параметры
postgres_source_url - jdbc:postgresql://nifi_demo_pg_src:5432/rms_demo
postgres_source_user - demo
postgres_source_password - demo
postgres_source_connections - 32
postgres_target_url - jdbc:postgresql://nifi_demo_pg_dst:5432/rms_demo
postgres_target_user - demo
postgres_target_password - demo
postgres_target_connections - 32
data_migration_config -
```
{
  "filters": {
    "documents_q1_2026": {
      "active": true,
      "schema": {
        "include": "^(bra|bsp|rca|ref)$"
      },
      "root": {
        "include": "^doc_.*$"
      },
      "filter": "root.tofk in ('6000','1800','6200','4800','9500') and root.document_date >= '2024-01-01'"
    },
    "all_dictionaries": {
      "active": true,
      "schema": {
        "include": "^(bra|bsp|rca|ref)$"
      },
      "root": {
        "include": "^dict_.*$"
      },
      "filter": "true"
    }
  },
  "select": {
    "default": {
      "lookahead": 100,
      "limit": 250
    },
    "bsp.doc_d_016": {
      "lookahead": 50
    },
    "bsp.doc_d_019": {
      "lookahead": 50
    }
  },
  "insert": {
    "attempts": 3,
    "split": true,
    "correct_bogus_ids": true,
    "skip_obsolete_dictionaries": true
  }
}

```
postgres_driver - /opt/nifi/nifi-current/lib/postgresql-42.7.9.jar

