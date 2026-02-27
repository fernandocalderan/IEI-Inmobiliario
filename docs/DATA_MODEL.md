# DATA MODEL - IEI Inmobiliario MVP

## 1) Principios
- Separar input crudo, resultado calculado y datos comerciales.
- Mantener trazabilidad para auditoria y calidad de leads.
- Permitir re-score futuro sin perder historico.

## 2) Entidades principales

### 2.1 `leads`
Representa el lead comercial del propietario.

Campos sugeridos:
- `id` UUID PK
- `status` enum: `nuevo|contactado|cita|vendido|descartado`
- `owner_name` text
- `owner_email` text
- `owner_phone` text
- `consent_contact` boolean not null
- `consent_text_version` text
- `consent_timestamp` timestamptz
- `source_campaign` text
- `utm_source` text
- `utm_medium` text
- `utm_campaign` text
- `utm_term` text
- `utm_content` text
- `ip_hash` text
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 2.2 `property_inputs`
Snapshot de `PropertyFeatures` del motor.

Campos:
- `id` UUID PK
- `lead_id` UUID FK -> `leads.id`
- `zone_key` text not null
- `municipality` text not null
- `neighborhood` text null
- `postal_code` text null
- `property_type` enum/text not null
- `m2` numeric(10,2) not null
- `condition` enum/text not null
- `year_built` int null
- `has_elevator` boolean not null default false
- `has_terrace` boolean not null default false
- `terrace_m2` numeric(10,2) null
- `has_parking` boolean not null default false
- `has_views` boolean not null default false
- `created_at` timestamptz not null

### 2.3 `owner_signals`
Snapshot de `OwnerSignals` del motor.

Campos:
- `id` UUID PK
- `lead_id` UUID FK -> `leads.id`
- `sale_horizon` enum/text not null
- `motivation` enum/text not null
- `already_listed` enum/text not null
- `exclusivity` enum/text not null
- `expected_price` numeric(14,2) null
- `created_at` timestamptz not null

### 2.4 `iei_results`
Resultado de `compute_iei` y `lead_card`.

Campos:
- `id` UUID PK
- `lead_id` UUID FK -> `leads.id`
- `iei_score` int not null
- `tier` char(1) not null
- `breakdown_intencion` int not null
- `breakdown_precio` int not null
- `breakdown_mercado` int not null
- `base_per_m2` numeric(12,2) not null
- `base_price` numeric(14,2) not null
- `adjusted_price` numeric(14,2) not null
- `range_low` numeric(14,2) not null
- `range_high` numeric(14,2) not null
- `demand_level` enum/text not null
- `pricing_expected_price` numeric(14,2) null
- `pricing_delta` numeric(8,5) null
- `pricing_gap_percent` numeric(6,2) null
- `pricing_note` text
- `recommendation` text not null
- `applied_factors_json` jsonb not null
- `lead_card_json` jsonb not null
- `engine_version` text not null
- `created_at` timestamptz not null

### 2.5 `zones`
Configuracion editable por zona.

Campos:
- `id` UUID PK
- `zone_key` text unique not null
- `municipality` text not null
- `base_per_m2` numeric(12,2) not null
- `demand_level` enum/text not null (`alta|media|baja`)
- `type_factor_overrides` jsonb null
- `condition_factor_overrides` jsonb null
- `extras_add_overrides` jsonb null
- `extras_cap_override` numeric(5,4) null
- `is_active` boolean not null default true
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

## 3) Relaciones
1. `leads` 1:1 `property_inputs`
2. `leads` 1:1 `owner_signals`
3. `leads` 1:N `iei_results` (permite recalculo historico)

## 4) Indices recomendados
- `leads(status, created_at desc)`
- `property_inputs(zone_key)`
- `owner_signals(sale_horizon, motivation)`
- `iei_results(tier, iei_score desc, created_at desc)`
- `zones(zone_key, is_active)`

## 5) Validaciones de datos
- `m2 > 0`
- `expected_price is null or expected_price > 0`
- `tier in ('A','B','C','D')`
- `consent_contact = true` para publicar lead a inmobiliaria

## 6) Auditoria minima
- `created_at`, `updated_at`
- `source_campaign`, `utm_*`
- `ip_hash`
- `engine_version` en `iei_results`

## 7) Campos previstos v2 (solo documentacion)

Estos campos se planifican para evolucion v2 y no implican cambios en el `schema.sql` actual del MVP.

1. `Lead.data_quality_flags` (json/array)
- Propuesta de almacenamiento: `leads.data_quality_flags` (jsonb).
- Uso: flags de consistencia y completitud del input.

2. `Lead.commercial_confidence` (FLOAT)
- Propuesta de almacenamiento: `leads.commercial_confidence` (FLOAT o numeric).
- Rango esperado: `0..1`.

3. `Lead.confidence_bucket` (VARCHAR)
- Propuesta de almacenamiento: `leads.confidence_bucket` (VARCHAR).
- Valores operativos sugeridos: `high|medium|low|unreliable`.

4. `PriceEstimate.adjusted_price_raw` (float)
- Propuesta de almacenamiento: `iei_results.adjusted_price_raw`.
- Uso: referencia no redondeada para calculos de `delta` en v2.

## Campos futuros refinados (prep V2)

Formalizacion para refinamientos pre-mercado (v2). No implica cambios en `schema.sql` ni contratos MVP vigentes.

### Nuevos campos documentados

- `Lead.data_quality_flags ARRAY<STRING>`
  Flags de validacion detallados.

- `Lead.commercial_confidence FLOAT`
  Score de calidad de dato.

- `Lead.confidence_bucket VARCHAR`
  Categoria de confidence.

- `PriceEstimate.adjusted_price_raw FLOAT`
  Precio ajustado sin redondeo para calculo interno de delta.
