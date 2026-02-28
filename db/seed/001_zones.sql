-- Seed zonas piloto IEI MVP

insert into zones (
  zone_key,
  municipality,
  base_per_m2,
  demand_level,
  zone_group,
  pricing_policy,
  pricing_json,
  is_premium,
  is_active
)
values
  (
    'castelldefels',
    'Castelldefels',
    3350.0,
    'alta',
    'baix_llobregat',
    'baix_llobregat_premium',
    jsonb_build_object(
      'A', 90,
      'B', 55,
      'C', 25,
      'D', 0,
      'A_PLUS', 150,
      'confidence', jsonb_build_object('high', 1.2, 'medium', 1.0, 'low', 0.8, 'unreliable', 0.0)
    ),
    true,
    true
  ),
  (
    'gava',
    'Gava',
    3100.0,
    'media',
    'baix_llobregat',
    'baix_llobregat_premium',
    jsonb_build_object(
      'A', 90,
      'B', 55,
      'C', 25,
      'D', 0,
      'A_PLUS', 150,
      'confidence', jsonb_build_object('high', 1.2, 'medium', 1.0, 'low', 0.8, 'unreliable', 0.0)
    ),
    true,
    true
  ),
  (
    'sitges',
    'Sitges',
    4100.0,
    'alta',
    'baix_llobregat',
    'baix_llobregat_premium',
    jsonb_build_object(
      'A', 90,
      'B', 55,
      'C', 25,
      'D', 0,
      'A_PLUS', 150,
      'confidence', jsonb_build_object('high', 1.2, 'medium', 1.0, 'low', 0.8, 'unreliable', 0.0)
    ),
    true,
    true
  )
on conflict (zone_key) do update set
  municipality = excluded.municipality,
  base_per_m2 = excluded.base_per_m2,
  demand_level = excluded.demand_level,
  zone_group = excluded.zone_group,
  pricing_policy = excluded.pricing_policy,
  pricing_json = excluded.pricing_json,
  is_premium = excluded.is_premium,
  is_active = excluded.is_active,
  updated_at = now();
