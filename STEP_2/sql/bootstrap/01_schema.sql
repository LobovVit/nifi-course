create extension if not exists pgcrypto;

create or replace function public.ulid_generate()
returns text
language sql
as $$
select upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 26));
$$;

create schema if not exists bra;
create schema if not exists bsp;
create schema if not exists rca;
create schema if not exists ref;

create table if not exists ref.dict_tofk (
  id text primary key,
  tofk text not null unique,
  name text not null,
  is_pilot boolean not null default false
);

create table if not exists bra.dict_doc_type (
  id text primary key,
  name text not null,
  is_active boolean not null default true
);

create table if not exists bra.dict_currency (
  id text primary key,
  name text not null,
  is_active boolean not null default true
);

create table if not exists bsp.dict_channel (
  id text primary key,
  name text not null,
  is_active boolean not null default true
);

create table if not exists rca.dict_region (
  id text primary key,
  name text not null,
  is_active boolean not null default true
);

create table if not exists bra.doc_d_001 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists bra.doc_d_001_line (
  id text primary key,
  parent_id text not null references bra.doc_d_001(id) on delete cascade,
  line_no integer not null,
  amount numeric(14,2) not null,
  currency_id text not null references bra.dict_currency(id)
);

create table if not exists bra.doc_d_001_note (
  id text primary key,
  parent_id text not null references bra.doc_d_001(id) on delete cascade,
  note_text text not null
);

create table if not exists bra.doc_d_023 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists bra.doc_d_023_item (
  id text primary key,
  parent_id text not null references bra.doc_d_023(id) on delete cascade,
  line_no integer not null,
  amount numeric(14,2) not null
);

create table if not exists bsp.doc_d_016 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists bsp.doc_d_016_step (
  id text primary key,
  parent_id text not null references bsp.doc_d_016(id) on delete cascade,
  step_no integer not null,
  channel_id text not null references bsp.dict_channel(id),
  details jsonb not null
);

create table if not exists bsp.doc_d_019 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists bsp.doc_d_019_entry (
  id text primary key,
  parent_id text not null references bsp.doc_d_019(id) on delete cascade,
  entry_no integer not null,
  amount numeric(14,2) not null,
  details jsonb not null
);

create table if not exists rca.doc_r_007 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists rca.doc_r_007_file (
  id text primary key,
  parent_id text not null references rca.doc_r_007(id) on delete cascade,
  file_name text not null,
  file_size integer not null
);

create table if not exists rca.doc_r_023 (
  id text primary key,
  created_date timestamp not null,
  document_date date not null,
  tofk text not null references ref.dict_tofk(tofk),
  status text not null,
  amount numeric(14,2) not null,
  payload jsonb not null
);

create table if not exists rca.doc_r_023_result (
  id text primary key,
  parent_id text not null references rca.doc_r_023(id) on delete cascade,
  result_code text not null,
  result_text text not null
);

create index if not exists ix_bra_doc_d_001_tofk_date on bra.doc_d_001 (tofk, document_date);
create index if not exists ix_bra_doc_d_023_tofk_date on bra.doc_d_023 (tofk, document_date);
create index if not exists ix_bsp_doc_d_016_tofk_date on bsp.doc_d_016 (tofk, document_date);
create index if not exists ix_bsp_doc_d_019_tofk_date on bsp.doc_d_019 (tofk, document_date);
create index if not exists ix_rca_doc_r_007_tofk_date on rca.doc_r_007 (tofk, document_date);
create index if not exists ix_rca_doc_r_023_tofk_date on rca.doc_r_023 (tofk, document_date);
