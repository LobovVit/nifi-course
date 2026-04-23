with root_counts as (
  select 'bra.doc_d_001' as table_name, count(*)::bigint as cnt
  from bra.doc_d_001 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
  union all
  select 'bra.doc_d_023', count(*) from bra.doc_d_023 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
  union all
  select 'bsp.doc_d_016', count(*) from bsp.doc_d_016 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
  union all
  select 'bsp.doc_d_019', count(*) from bsp.doc_d_019 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
  union all
  select 'rca.doc_r_007', count(*) from rca.doc_r_007 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
  union all
  select 'rca.doc_r_023', count(*) from rca.doc_r_023 root
  where root.tofk in ('6000','1800','6200','4800','9500')
    and root.document_date >= '2026-01-01'
    and root.document_date < '2026-04-01'
)
select * from root_counts order by 1;
