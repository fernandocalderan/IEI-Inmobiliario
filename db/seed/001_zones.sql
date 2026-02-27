-- Seed zonas piloto IEI MVP

insert into zones (zone_key, municipality, base_per_m2, demand_level, is_active)
values
  ('castelldefels', 'Castelldefels', 3350.0, 'alta', true),
  ('gava', 'Gava', 3100.0, 'media', true),
  ('sitges', 'Sitges', 4100.0, 'alta', true)
on conflict (zone_key) do update set
  municipality = excluded.municipality,
  base_per_m2 = excluded.base_per_m2,
  demand_level = excluded.demand_level,
  is_active = excluded.is_active,
  updated_at = now();
