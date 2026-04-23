import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

import psycopg2
import psycopg2.extras
import ulid
from faker import Faker

fake = Faker("ru_RU")
random.seed(42)

PILOT_TOFKS = ["6000", "1800", "6200", "4800", "9500"]
OTHER_TOFKS = ["2800", "9999", "7700"]
ALL_TOFKS = PILOT_TOFKS + OTHER_TOFKS
STATUSES = ["CREATED", "SIGNED", "SENT", "ARCHIVED", "CANCELLED"]

ROOT_ROWS_PER_TABLE = int(os.getenv("ROOT_ROWS_PER_TABLE", "120"))
MAX_CHILD_ROWS = int(os.getenv("MAX_CHILD_ROWS", "5"))
DEMO_YEAR = int(os.getenv("DEMO_YEAR", "2026"))
FORCE_RECREATE = os.getenv("FORCE_RECREATE", "false").lower() == "true"

Q1_START = date(DEMO_YEAR, 1, 1)
Q1_END = date(DEMO_YEAR, 3, 31)

ROOT_TABLES = [
    ("bra", "doc_d_001", "line", "note"),
    ("bra", "doc_d_023", "item", None),
    ("bsp", "doc_d_016", "step", None),
    ("bsp", "doc_d_019", "entry", None),
    ("rca", "doc_r_007", "file", None),
    ("rca", "doc_r_023", "result", None),
]

def conn_from(prefix: str):
    return psycopg2.connect(
        host=os.getenv(f"{prefix}_PGHOST"),
        port=int(os.getenv(f"{prefix}_PGPORT", "5432")),
        dbname=os.getenv(f"{prefix}_PGDATABASE", "rms_demo"),
        user=os.getenv(f"{prefix}_PGUSER", "demo"),
        password=os.getenv(f"{prefix}_PGPASSWORD", "demo"),
    )

def new_ulid(dt: datetime | None = None) -> str:
    if dt is None:
        return str(ulid.new())
    return str(ulid.from_timestamp(dt.timestamp()))

def q1_date():
    return fake.date_between_dates(date_start=Q1_START, date_end=Q1_END)

def random_doc_date():
    bucket = random.random()
    if bucket < 0.55:
        return q1_date()
    if bucket < 0.80:
        return fake.date_between_dates(date_start=date(DEMO_YEAR, 4, 1), date_end=date(DEMO_YEAR, 12, 31))
    return fake.date_between_dates(date_start=date(DEMO_YEAR - 2, 1, 1), date_end=date(DEMO_YEAR - 1, 12, 31))

def random_tofk():
    return random.choice(PILOT_TOFKS if random.random() < 0.70 else ALL_TOFKS)

def random_created_ts(doc_date: date) -> datetime:
    return datetime(doc_date.year, doc_date.month, doc_date.day, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))

def reset_data(conn):
    cur = conn.cursor()
    cur.execute("""
        truncate table
          bra.doc_d_001_line,
          bra.doc_d_001_note,
          bra.doc_d_001,
          bra.doc_d_023_item,
          bra.doc_d_023,
          bsp.doc_d_016_step,
          bsp.doc_d_016,
          bsp.doc_d_019_entry,
          bsp.doc_d_019,
          rca.doc_r_007_file,
          rca.doc_r_007,
          rca.doc_r_023_result,
          rca.doc_r_023,
          ref.dict_tofk,
          bra.dict_doc_type,
          bra.dict_currency,
          bsp.dict_channel,
          rca.dict_region
        restart identity cascade
    """)
    conn.commit()
    cur.close()

def seed_dicts(conn):
    cur = conn.cursor()
    cur.executemany(
        """insert into ref.dict_tofk(id, tofk, name, is_pilot)
        values (%s, %s, %s, %s)
        on conflict (id) do update
          set tofk = excluded.tofk,
              name = excluded.name,
              is_pilot = excluded.is_pilot""",
        [(f"TOFK_{t}", t, f"ТОФК {t}", t in PILOT_TOFKS) for t in ALL_TOFKS],
    )
    cur.executemany(
        "insert into bra.dict_doc_type(id, name) values (%s, %s) on conflict (id) do update set name = excluded.name",
        [("PAYMENT", "Платёж"), ("REQUEST", "Запрос"), ("REPORT", "Отчёт")],
    )
    cur.executemany(
        "insert into bra.dict_currency(id, name) values (%s, %s) on conflict (id) do update set name = excluded.name",
        [("RUB", "Российский рубль"), ("USD", "Доллар США"), ("EUR", "Евро")],
    )
    cur.executemany(
        "insert into bsp.dict_channel(id, name) values (%s, %s) on conflict (id) do update set name = excluded.name",
        [("WEB", "Web"), ("API", "API"), ("FILE", "File")],
    )
    cur.executemany(
        "insert into rca.dict_region(id, name) values (%s, %s) on conflict (id) do update set name = excluded.name",
        [("VOLGA", "Приволжье"), ("URAL", "Урал"), ("CENTER", "Центр")],
    )
    conn.commit()
    cur.close()

def seed_root_docs(cur, schema: str, table: str):
    rows = []
    ids = []
    for i in range(ROOT_ROWS_PER_TABLE):
        doc_date = random_doc_date()
        created_ts = random_created_ts(doc_date)
        doc_id = new_ulid(created_ts + timedelta(milliseconds=i))
        ids.append((doc_id, doc_date))
        rows.append((
            doc_id,
            created_ts,
            doc_date,
            random_tofk(),
            random.choice(STATUSES),
            Decimal(str(round(random.uniform(1000, 500000), 2))),
            psycopg2.extras.Json({
                "title": fake.sentence(nb_words=5),
                "owner": fake.company(),
                "doc_type": random.choice(["PAYMENT", "REQUEST", "REPORT"]),
                "comment": fake.text(max_nb_chars=80),
            })
        ))
    cur.executemany(
        f"insert into {schema}.{table}(id, created_date, document_date, tofk, status, amount, payload) values (%s,%s,%s,%s,%s,%s,%s)",
        rows,
    )
    return ids

def seed_child_rows(cur, schema: str, table: str, suffix: str, ids):
    child_table = f"{schema}.{table}_{suffix}"
    rows = []
    for parent_id, doc_date in ids:
        for idx in range(1, random.randint(1, MAX_CHILD_ROWS) + 1):
            child_id = new_ulid(datetime(doc_date.year, doc_date.month, doc_date.day, 12, 0, 0) + timedelta(milliseconds=idx))
            if suffix == "line":
                rows.append((child_id, parent_id, idx, Decimal(str(round(random.uniform(100, 10000), 2))), random.choice(["RUB", "USD", "EUR"])))
            elif suffix == "note":
                rows.append((child_id, parent_id, fake.sentence(nb_words=8)))
            elif suffix == "item":
                rows.append((child_id, parent_id, idx, Decimal(str(round(random.uniform(100, 5000), 2)))))
            elif suffix == "step":
                rows.append((child_id, parent_id, idx, random.choice(["WEB", "API", "FILE"]), psycopg2.extras.Json({"step": idx, "description": fake.sentence(nb_words=6)})))
            elif suffix == "entry":
                rows.append((child_id, parent_id, idx, Decimal(str(round(random.uniform(100, 7000), 2))), psycopg2.extras.Json({"entry": idx, "purpose": fake.word()})))
            elif suffix == "file":
                rows.append((child_id, parent_id, f"{fake.word()}.pdf", random.randint(10_000, 1_000_000)))
            elif suffix == "result":
                rows.append((child_id, parent_id, random.choice(["OK", "WARN", "ERR"]), fake.sentence(nb_words=6)))
    if not rows:
        return

    if suffix == "line":
        cur.executemany(f"insert into {child_table}(id, parent_id, line_no, amount, currency_id) values (%s,%s,%s,%s,%s)", rows)
    elif suffix == "note":
        cur.executemany(f"insert into {child_table}(id, parent_id, note_text) values (%s,%s,%s)", rows)
    elif suffix == "item":
        cur.executemany(f"insert into {child_table}(id, parent_id, line_no, amount) values (%s,%s,%s,%s)", rows)
    elif suffix == "step":
        cur.executemany(f"insert into {child_table}(id, parent_id, step_no, channel_id, details) values (%s,%s,%s,%s,%s)", rows)
    elif suffix == "entry":
        cur.executemany(f"insert into {child_table}(id, parent_id, entry_no, amount, details) values (%s,%s,%s,%s,%s)", rows)
    elif suffix == "file":
        cur.executemany(f"insert into {child_table}(id, parent_id, file_name, file_size) values (%s,%s,%s,%s)", rows)
    elif suffix == "result":
        cur.executemany(f"insert into {child_table}(id, parent_id, result_code, result_text) values (%s,%s,%s,%s)", rows)

def seed_source(conn):
    if FORCE_RECREATE:
        reset_data(conn)
    seed_dicts(conn)

    cur = conn.cursor()
    summary = {}
    for schema, root, child1, child2 in ROOT_TABLES:
        ids = seed_root_docs(cur, schema, root)
        seed_child_rows(cur, schema, root, child1, ids)
        if child2:
            seed_child_rows(cur, schema, root, child2, ids)
        summary[f"{schema}.{root}"] = len(ids)
    conn.commit()
    cur.close()
    return summary

def print_summary(conn, label):
    cur = conn.cursor()
    queries = [
        ("ref.dict_tofk", "select count(*) from ref.dict_tofk"),
        ("bra.dict_doc_type", "select count(*) from bra.dict_doc_type"),
        ("bra.doc_d_001", "select count(*) from bra.doc_d_001"),
        ("bra.doc_d_023", "select count(*) from bra.doc_d_023"),
        ("bsp.doc_d_016", "select count(*) from bsp.doc_d_016"),
        ("bsp.doc_d_019", "select count(*) from bsp.doc_d_019"),
        ("rca.doc_r_007", "select count(*) from rca.doc_r_007"),
        ("rca.doc_r_023", "select count(*) from rca.doc_r_023"),
    ]
    print(f"\n[{label}] Snapshot")
    for name, sql in queries:
        cur.execute(sql)
        print(f"  {name:<20} {cur.fetchone()[0]}")
    cur.close()

def main():
    src = conn_from("SRC")
    dst = conn_from("DST")
    try:
        seed_dicts(dst)
        summary = seed_source(src)
        print("[SRC] Seeded root docs:", summary)
        print_summary(src, "SRC")
        print_summary(dst, "DST (before migration)")
        print("\nDone. Source is filled, target has empty doc tables and ready dictionaries.")
        print(f"Expected filter window: pilots {PILOT_TOFKS} and document_date between {Q1_START} and {Q1_END}.")
    finally:
        src.close()
        dst.close()

if __name__ == "__main__":
    main()
