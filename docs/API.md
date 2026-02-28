# API CONTRACT - IEI Inmobiliario MVP

## 1) Compatibilidad
- Contratos MVP se mantienen.
- Extensiones de framework son aditivas y opcionales.

## 2) `POST /api/iei/score`
Response incluye, además de MVP:

```json
{
  "iei_framework": {
    "name": "IEI™",
    "full_name": "IEI™ — Índice de Evaluación Integral",
    "tagline": "Framework propietario de evaluación determinista, versionado y auditable.",
    "version": "1.0"
  }
}
```

Campo opcional (backward compatible).

## 3) `POST /api/leads`
Response 201 incluye, además de MVP:

```json
{
  "iei_framework": {
    "name": "IEI™",
    "full_name": "IEI™ — Índice de Evaluación Integral",
    "tagline": "Framework propietario de evaluación determinista, versionado y auditable.",
    "version": "1.0"
  },
  "lead_card": {
    "iei_framework": {
      "name": "IEI™",
      "full_name": "IEI™ — Índice de Evaluación Integral",
      "tagline": "Framework propietario de evaluación determinista, versionado y auditable.",
      "version": "1.0"
    },
    "powered_by": "Powered by IEI™"
  }
}
```

## 4) `GET /api/admin/sales/export.csv`
Columnas adicionales:
- `iei_framework_version`
- `powered_by`

Sin eliminar columnas existentes.

## 5) Notas de naming
- IEI se documenta como tecnología propietaria.
- La capa comercial/branding no altera scoring del motor.

## 6) Campos v2 (sin implementación actual)
- `price_estimate.adjusted_price_raw`
- `pricing_alignment.delta_raw`
- `lead_card.data_quality_flags[]`
- `lead_card.commercial_confidence`
- `lead_card.confidence_bucket`
