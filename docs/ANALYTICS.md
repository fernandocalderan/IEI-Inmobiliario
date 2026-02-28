# ANALYTICS - IEI Inmobiliario MVP

## 1) Eventos mínimos
- `view_landing`
- `start_form`
- `step_complete`
- `submit_lead`
- `view_result`
- `call_requested`

## 2) Propiedades requeridas
- `session_id` obligatorio
- `event_version` obligatorio
- dedupe `submit_lead` por `lead_id`

## 3) Propiedades de framework (opcionales)
En eventos de resultado/envío se recomienda incluir:
- `iei_framework_version`

## 4) Métricas negocio
- CPL
- completion rate
- `% tier A/B`
- `% A_PLUS`
- revenue por `pricing_policy`
- revenue por `segment`
- tasa de cita y cierre por tier

## 5) Calibración
- `lead_to_appointment_rate` por tier
- `exclusiva_firmada_rate` por tier
- `win_rate` por zona
- correlación `gap_percent` vs cierre
- segmentación futura por `confidence_bucket`
