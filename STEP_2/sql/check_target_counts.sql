select 'bra.doc_d_001' as table_name, count(*) from bra.doc_d_001
union all select 'bra.doc_d_023', count(*) from bra.doc_d_023
union all select 'bsp.doc_d_016', count(*) from bsp.doc_d_016
union all select 'bsp.doc_d_019', count(*) from bsp.doc_d_019
union all select 'rca.doc_r_007', count(*) from rca.doc_r_007
union all select 'rca.doc_r_023', count(*) from rca.doc_r_023
union all select 'ref.dict_tofk', count(*) from ref.dict_tofk
union all select 'bra.dict_doc_type', count(*) from bra.dict_doc_type
union all select 'bra.dict_currency', count(*) from bra.dict_currency
union all select 'bsp.dict_channel', count(*) from bsp.dict_channel
union all select 'rca.dict_region', count(*) from rca.dict_region
order by 1;
