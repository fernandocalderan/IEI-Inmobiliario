-- Premium pricing policy for Baix Llobregat

alter table leads add column if not exists pricing_policy text;
alter table leads add column if not exists is_premium_zone boolean not null default false;
alter table leads add column if not exists lead_price_eur numeric(10,2);
alter table leads add column if not exists segment text;
alter table leads add column if not exists confidence_bucket text;

alter table zones add column if not exists zone_group text;
alter table zones add column if not exists pricing_policy text;
alter table zones add column if not exists pricing_json jsonb;
alter table zones add column if not exists is_premium boolean not null default false;

alter table iei_results add column if not exists pricing_json jsonb;

create index if not exists idx_leads_pricing_policy_segment on leads (pricing_policy, segment);
create index if not exists idx_leads_price_eur on leads (lead_price_eur);
create index if not exists idx_zones_premium_policy on zones (is_premium, pricing_policy);
