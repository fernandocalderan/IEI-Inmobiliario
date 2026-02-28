# DATA MODEL - IEI Inmobiliario MVP

## 1) Modelo base
- `leads`
- `property_inputs`
- `owner_signals`
- `iei_results`
- `zones`
- operación comercial: `agencies`, `lead_reservations`, `lead_sales`, `events`

## 2) Metadatos IEI framework (sin migración nueva)
Como ya existe `iei_results.lead_card_json`, se persiste ahí:

```json
{
  "iei_framework": {
    "name": "IEI™",
    "full_name": "IEI™ — Índice de Evaluación Integral",
    "tagline": "Framework propietario de evaluación determinista, versionado y auditable.",
    "version": "1.0"
  },
  "powered_by": "Powered by IEI™"
}
```

## 3) Export/comercial
En export de ventas se añade:
- `iei_framework_version`
- `powered_by`

## 4) Versiones
- `engine_version`: versión de cálculo del motor.
- `framework_version`: versión semántica del framework IEI™ mostrado.

## 5) Campos futuros (v2)
- `Lead.data_quality_flags`
- `Lead.commercial_confidence`
- `Lead.confidence_bucket`
- `PriceEstimate.adjusted_price_raw`
