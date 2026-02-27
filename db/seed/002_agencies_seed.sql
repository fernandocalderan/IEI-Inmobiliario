insert into agencies (id, name, email, phone, municipality_focus, is_active)
values
  ('00000000-0000-0000-0000-000000000101', 'Agencia Costa Norte', 'ventas@costanorte.example', '+34930000001', 'castelldefels', true),
  ('00000000-0000-0000-0000-000000000102', 'Gava Habitat', 'ops@gavahabitat.example', '+34930000002', 'gava', true),
  ('00000000-0000-0000-0000-000000000103', 'Sitges Prime Homes', 'leads@sitgesprime.example', '+34930000003', 'sitges', true)
on conflict (id) do update set
  name = excluded.name,
  email = excluded.email,
  phone = excluded.phone,
  municipality_focus = excluded.municipality_focus,
  is_active = excluded.is_active;
