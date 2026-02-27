# ANALYTICS - IEI Inmobiliario MVP

## 1) Objetivo
Medir eficiencia de captacion, calidad de leads y rendimiento comercial de leads premium.

## 2) Eventos minimos

1. `view_landing`
- Cuando se muestra landing.
- Props: `source_campaign`, `utm_*`, `session_id`.

2. `start_form`
- Primer input del formulario.
- Props: `zone_key` (si ya disponible), `session_id`.

3. `step_complete`
- Fin de cada paso.
- Props: `step_name` (`property|signals|price|contact`), `duration_ms`, `session_id`.

4. `submit_lead`
- Submit final con consentimiento.
- Props: `zone_key`, `sale_horizon`, `motivation`, `expected_price_present`.

5. `view_result`
- Visualizacion del informe.
- Props: `iei_score`, `tier`, `gap_percent`, `zone_key`.

6. `call_requested`
- Solicitud activa de llamada/contacto.
- Props: `lead_id`, `tier`, `zone_key`.

## 3) Metricas de negocio

1. CPL
- `coste_campana / numero_leads`

2. Completion rate
- `submit_lead / start_form`

3. `% Tier A/B`
- `(leads tier A + B) / leads totales`

4. Coste por premium
- `coste_campana / leads tier A/B`

5. Tasa de contacto
- `leads_contactados / leads_totales`

6. Tasa de cita
- `leads_con_cita / leads_contactados`

7. Recompra inmobiliaria
- `% agencias que compran >1 lote de leads`

## 4) Segmentaciones minimas
- Por `zone_key`
- Por `sale_horizon`
- Por fuente (`utm_source`, `utm_campaign`)
- Por tier

## 5) Calidad de dato
- Rechazar eventos sin `session_id`.
- Deduplicacion de `submit_lead` por `lead_id`.
- Versionar esquema de evento (`event_version`).

## 6) Calibracion del IEI

### Metricas de calibracion
1. `lead_to_appointment_rate` por tier.
2. `exclusiva_firmada_rate` por tier.
3. `win_rate` por zona.
4. Relacion `gap_percent` vs cierre.
5. Segmentacion futura por `confidence_bucket`.

### Lectura operativa esperada
- Tier A debe sostener mejor conversion a cita que Tier B.
- `gap_percent` alto debe correlacionar con menor cierre.
- `confidence_bucket` se incorporara cuando exista `commercial_confidence` en v2.

## 7) Metricas de pricing (v2)

1. Revenue por Tier
- Ingreso agregado por `tier` en periodo.

2. Revenue por `confidence_bucket`
- Ingreso agregado por bucket de confianza (`high|medium|low|unreliable`).

3. Refund rate por bucket
- `% leads reembolsados / leads vendidos` por `confidence_bucket`.

4. LTV agencia por tier consumido
- Valor acumulado por agencia segmentado por mezcla de tiers comprados.

### Estado
- Metricas previstas para la fase de comercializacion v2, no activas en MVP actual.

## Metricas adicionales para refinamiento pre-mercado (v2)

Formalizacion para refinamientos pre-mercado (v2), sin cambios sobre contratos MVP actuales.

### Validacion de calidad de lead
- `count_leads_by_flag(M2_INVALID)`
- `count_leads_by_flag(M2_OUTLIER)`
- `count_leads_by_flag(MISSING_EXPECTED_PRICE)`
- `count_leads_by_flag(ZONE_UNKNOWN)`

### Efecto de confidence en conversion
- `appointment_rate_by_confidence_bucket`
- `exclusivity_rate_by_confidence_bucket`
- `close_rate_by_confidence_bucket`

### Lead pricing performance
- `revenue_per_tier_bucket`
- `refund_rate_per_bucket`
- `LTV_by_tier_and_confidence`
