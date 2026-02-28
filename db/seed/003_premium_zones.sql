-- Premium pricing seed for Baix Llobregat

update zones
set
  zone_group = 'baix_llobregat',
  pricing_policy = 'baix_llobregat_premium',
  pricing_json = jsonb_build_object(
    'A', 90,
    'B', 55,
    'C', 25,
    'D', 0,
    'A_PLUS', 150,
    'confidence', jsonb_build_object(
      'high', 1.2,
      'medium', 1.0,
      'low', 0.8,
      'unreliable', 0.0
    )
  ),
  is_premium = true,
  updated_at = now()
where zone_key in ('castelldefels', 'gava', 'sitges');
