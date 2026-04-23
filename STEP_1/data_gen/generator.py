import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras
from faker import Faker

fake = Faker()

TOFK_VALUES = ["6000", "2800", "9999"]
DOC_STATUSES = ["CREATED", "SIGNED", "SENT", "ARCHIVED"]
DOC_TYPES = ["PAYMENT", "CONTRACT", "REQUEST"]

ROWS_PER_DOC_TABLE = int(os.getenv("ROWS_PER_DOC_TABLE", "200"))
MAX_LINKS_PER_DOC = int(os.getenv("MAX_LINKS_PER_DOC", "3"))

DDL = """
create schema if not exists bra;

create table if not exists bra.ref_tofk (
  tofk text primary key,
  name text not null
);

create table if not exists bra.doc_d_001 (
  id uuid primary key,
  created_date timestamp not null,
  tofk text not null references bra.ref_tofk(tofk),
  doc_type text not null,
  status text not null,
  payload jsonb not null
);

create table if not exists bra.doc_d_002 (
  id uuid primary key,
  created_date timestamp not null,
  tofk text not null references bra.ref_tofk(tofk),
  doc_type text not null,
  status text not null,
  payload jsonb not null
);

create table if not exists bra.doc_d_003 (
  id uuid primary key,
  created_date timestamp not null,
  tofk text not null references bra.ref_tofk(tofk),
  doc_type text not null,
  status text not null,
  payload jsonb not null
);

create table if not exists bra.doc_links_001 (
  id uuid primary key,
  doc_id uuid not null references bra.doc_d_001(id) on delete cascade,
  link_type text not null,
  target_id uuid not null
);

create table if not exists bra.doc_links_002 (
  id uuid primary key,
  doc_id uuid not null references bra.doc_d_002(id) on delete cascade,
  link_type text not null,
  target_id uuid not null
);

create table if not exists bra.doc_links_003 (
  id uuid primary key,
  doc_id uuid not null references bra.doc_d_003(id) on delete cascade,
  link_type text not null,
  target_id uuid not null
);

create table if not exists bra.audit_log (
  id bigserial primary key,
  created_at timestamp not null,
  level text not null,
  message text not null
);
"""

def conn_from(prefix: str):
    return psycopg2.connect(
        host=os.getenv(f"{prefix}_PGHOST"),
        port=int(os.getenv(f"{prefix}_PGPORT", "5432")),
        dbname=os.getenv(f"{prefix}_PGDATABASE", "demo"),
        user=os.getenv(f"{prefix}_PGUSER", "demo"),
        password=os.getenv(f"{prefix}_PGPASSWORD", "demo"),
    )

def random_created_date():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 12, 31, tzinfo=timezone.utc)
    delta = end - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).replace(tzinfo=None)

def apply_ddl(conn, label: str):
    conn.autocommit = True
    cur = conn.cursor()
    print(f"[{label}] Applying DDL...")
    cur.execute(DDL)
    cur.close()

def seed_source(conn):
    conn.autocommit = True
    cur = conn.cursor()
    print("[SRC] Seeding ref_tofk ...")
    cur.executemany(
        "insert into bra.ref_tofk(tofk, name) values (%s, %s) on conflict (tofk) do nothing",
        [(t, f"TOFK {t}") for t in TOFK_VALUES],
    )

    def insert_docs(table_name: str):
        rows = []
        ids = []
        for _ in range(ROWS_PER_DOC_TABLE):
            doc_id = uuid.uuid4()
            ids.append(doc_id)
            created = random_created_date()
            tofk = random.choice(TOFK_VALUES)
            doc_type = random.choice(DOC_TYPES)
            status = random.choice(DOC_STATUSES)
            payload = {
                "title": fake.sentence(nb_words=6),
                "amount": round(random.uniform(10, 50000), 2),
                "counterparty": fake.company(),
            }
            rows.append((str(doc_id), created, tofk, doc_type, status, psycopg2.extras.Json(payload)))

        cur.executemany(
            f"insert into {table_name}(id, created_date, tofk, doc_type, status, payload) values (%s,%s,%s,%s,%s,%s)",
            rows,
        )
        return ids

    print("[SRC] Inserting docs into bra.doc_d_001 ...")
    d1_ids = insert_docs("bra.doc_d_001")

    print("[SRC] Inserting docs into bra.doc_d_002 ...")
    d2_ids = insert_docs("bra.doc_d_002")

    print("[SRC] Inserting docs into bra.doc_d_003 ...")
    d3_ids = insert_docs("bra.doc_d_003")

    def insert_links(links_table: str, doc_ids):
        rows = []
        for doc_id in doc_ids:
            for _ in range(random.randint(0, MAX_LINKS_PER_DOC)):
                rows.append((str(uuid.uuid4()), str(doc_id), random.choice(["PARENT", "CHILD", "RELATED"]), str(uuid.uuid4())))
        if rows:
            cur.executemany(
                f"insert into {links_table}(id, doc_id, link_type, target_id) values (%s,%s,%s,%s)",
                rows,
            )

    print("[SRC] Inserting links into bra.doc_links_001 ...")
    insert_links("bra.doc_links_001", random.sample(d1_ids, k=min(len(d1_ids), ROWS_PER_DOC_TABLE)))

    print("[SRC] Inserting links into bra.doc_links_002 ...")
    insert_links("bra.doc_links_002", random.sample(d2_ids, k=min(len(d2_ids), ROWS_PER_DOC_TABLE)))

    print("[SRC] Inserting links into bra.doc_links_003 ...")
    insert_links("bra.doc_links_003", random.sample(d3_ids, k=min(len(d3_ids), ROWS_PER_DOC_TABLE)))

    print("[SRC] Inserting audit logs ...")
    now = datetime.now().replace(tzinfo=None)
    log_rows = [(now - timedelta(minutes=i), random.choice(["INFO", "WARN", "ERROR"]), fake.sentence(nb_words=10)) for i in range(ROWS_PER_DOC_TABLE)]
    cur.executemany(
        "insert into bra.audit_log(created_at, level, message) values (%s,%s,%s)",
        log_rows,
    )

    cur.close()

def main():
    src = conn_from("SRC")
    dst = conn_from("DST")

    try:
        apply_ddl(src, "SRC")
        apply_ddl(dst, "DST")
        seed_source(src)
        print("Done. SAME structures created in pg_src and pg_dst. Data seeded ONLY in pg_src.")
    finally:
        src.close()
        dst.close()

if __name__ == "__main__":
    main()
