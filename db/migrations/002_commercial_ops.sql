-- Sprint A - Commercial Ops MVP
-- Reservas, ventas y dedupe de leads

alter table leads add column if not exists phone_hash text;
create index if not exists idx_leads_phone_hash_created_at on leads (phone_hash, created_at desc);

create table if not exists agencies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text,
  phone text,
  municipality_focus text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists lead_reservations (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null unique references leads(id) on delete cascade,
  agency_id uuid not null references agencies(id),
  reserved_at timestamptz not null default now(),
  reserved_until timestamptz not null,
  status text not null default 'active' check (status in ('active','released','expired')),
  released_at timestamptz
);

create index if not exists idx_lead_reservations_agency on lead_reservations (agency_id);
create index if not exists idx_lead_reservations_until on lead_reservations (reserved_until);
create index if not exists idx_lead_reservations_status on lead_reservations (status);

create table if not exists lead_sales (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null unique references leads(id) on delete cascade,
  agency_id uuid not null references agencies(id),
  sold_at timestamptz not null default now(),
  tier text not null,
  price_eur integer not null,
  notes text
);

create index if not exists idx_lead_sales_agency on lead_sales (agency_id);
create index if not exists idx_lead_sales_sold_at on lead_sales (sold_at);
create index if not exists idx_lead_sales_tier on lead_sales (tier);
