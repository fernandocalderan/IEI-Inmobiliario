-- Schema MVP para Informe de Ventabilidad Inmobiliaria

create extension if not exists "pgcrypto";

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  status text not null default 'nuevo' check (status in ('nuevo','contactado','cita','vendido','descartado')),
  owner_name text,
  owner_email text,
  owner_phone text,
  consent_contact boolean not null,
  consent_text_version text,
  consent_timestamp timestamptz,
  source_campaign text,
  utm_source text,
  utm_medium text,
  utm_campaign text,
  utm_term text,
  utm_content text,
  ip_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists property_inputs (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null unique references leads(id) on delete cascade,
  zone_key text not null,
  municipality text not null,
  neighborhood text,
  postal_code text,
  property_type text not null check (property_type in ('piso','atico','planta_baja','casa_adosada','chalet')),
  m2 numeric(10,2) not null check (m2 > 0),
  condition text not null check (condition in ('reformado','buen_estado','a_reformar_parcial','a_reformar_integral')),
  year_built int,
  has_elevator boolean not null default false,
  has_terrace boolean not null default false,
  terrace_m2 numeric(10,2),
  has_parking boolean not null default false,
  has_views boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists owner_signals (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null unique references leads(id) on delete cascade,
  sale_horizon text not null check (sale_horizon in ('<3m','3-6m','6-12m','valorando')),
  motivation text not null check (motivation in ('traslado','herencia','divorcio','finanzas','mejora','compra_otra','inversion','curiosidad','otro')),
  already_listed text not null check (already_listed in ('no','si_con_agencia','si_por_su_cuenta')),
  exclusivity text not null check (exclusivity in ('si','depende','no')),
  expected_price numeric(14,2) check (expected_price is null or expected_price > 0),
  created_at timestamptz not null default now()
);

create table if not exists iei_results (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references leads(id) on delete cascade,
  iei_score int not null check (iei_score >= 0 and iei_score <= 100),
  tier text not null check (tier in ('A','B','C','D')),
  breakdown_intencion int not null,
  breakdown_precio int not null,
  breakdown_mercado int not null,
  base_per_m2 numeric(12,2) not null,
  base_price numeric(14,2) not null,
  adjusted_price numeric(14,2) not null,
  range_low numeric(14,2) not null,
  range_high numeric(14,2) not null,
  demand_level text not null check (demand_level in ('alta','media','baja')),
  pricing_expected_price numeric(14,2),
  pricing_delta numeric(8,5),
  pricing_gap_percent numeric(6,2),
  pricing_note text,
  recommendation text not null,
  applied_factors_json jsonb not null,
  lead_card_json jsonb not null,
  engine_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists zones (
  id uuid primary key default gen_random_uuid(),
  zone_key text not null unique,
  municipality text not null,
  base_per_m2 numeric(12,2) not null,
  demand_level text not null check (demand_level in ('alta','media','baja')),
  type_factor_overrides jsonb,
  condition_factor_overrides jsonb,
  extras_add_overrides jsonb,
  extras_cap_override numeric(5,4),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_leads_status_created_at on leads(status, created_at desc);
create index if not exists idx_property_inputs_zone_key on property_inputs(zone_key);
create index if not exists idx_owner_signals_horizon_motivation on owner_signals(sale_horizon, motivation);
create index if not exists idx_iei_results_tier_score_created_at on iei_results(tier, iei_score desc, created_at desc);
create index if not exists idx_zones_zone_key_active on zones(zone_key, is_active);
