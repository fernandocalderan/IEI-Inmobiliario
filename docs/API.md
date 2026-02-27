# API CONTRACT - IEI Inmobiliario MVP

## 1) Convenciones
- Base path: `/api`
- Content-Type: `application/json`
- Errores con formato:
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "mensaje legible",
    "details": {}
  }
}
```

## 2) Enums del motor (exactos)

### PropertyType
- `piso`
- `atico`
- `planta_baja`
- `casa_adosada`
- `chalet`

### PropertyCondition
- `reformado`
- `buen_estado`
- `a_reformar_parcial`
- `a_reformar_integral`

### SaleHorizon
- `<3m`
- `3-6m`
- `6-12m`
- `valorando`

### Motivation
- `traslado`
- `herencia`
- `divorcio`
- `finanzas`
- `mejora`
- `compra_otra`
- `inversion`
- `curiosidad`
- `otro`

### ListingStatus
- `no`
- `si_con_agencia`
- `si_por_su_cuenta`

### ExclusivityDisposition
- `si`
- `depende`
- `no`

## 3) POST `/api/iei/score`
Calcula `IEIResult` sin crear lead comercial.

### Request (LeadInput)
```json
{
  "property": {
    "zone_key": "castelldefels",
    "municipality": "Castelldefels",
    "neighborhood": "Centro",
    "postal_code": "08860",
    "property_type": "piso",
    "m2": 90,
    "condition": "buen_estado",
    "year_built": 1998,
    "has_elevator": true,
    "has_terrace": true,
    "terrace_m2": 8,
    "has_parking": false,
    "has_views": false
  },
  "owner": {
    "sale_horizon": "3-6m",
    "motivation": "compra_otra",
    "already_listed": "no",
    "exclusivity": "depende",
    "expected_price": 380000
  }
}
```

### Response 200 (IEIResult)
```json
{
  "iei_score": 63,
  "tier": "C",
  "breakdown": {
    "intencion": 29,
    "precio": 6,
    "mercado": 28
  },
  "price_estimate": {
    "base_per_m2": 3350.0,
    "base_price": 301500.0,
    "adjusted_price": 319500.0,
    "range_low": 310000.0,
    "range_high": 335500.0,
    "demand_level": "alta",
    "applied_factors": {
      "type": 1.0,
      "condition": 1.0,
      "extra_elevator": 1.04,
      "extra_terrace": 1.02,
      "extras_factor_capped": 1.06
    }
  },
  "pricing_alignment": {
    "expected_price": 380000.0,
    "estimated_range": [310000.0, 335500.0],
    "delta": 0.18935837245696402,
    "gap_percent": 18.9,
    "note": "Expectativa por encima del mercado: puede alargar venta."
  },
  "recommendation": "Ventabilidad media. Expectativa por encima del mercado: puede alargar venta. Recomendado ajustar expectativas y mejorar presentación antes de salir al mercado."
}
```

### Errores
1. 400 `VALIDATION_ERROR`
- Campos invalidos o enums fuera de contrato.

2. 422 `ZONE_NOT_CONFIGURED`
```json
{
  "error": {
    "code": "ZONE_NOT_CONFIGURED",
    "message": "Zona no configurada: badalona",
    "details": {
      "zone_key": "badalona"
    }
  }
}
```

## 4) POST `/api/leads`
Crea lead, persiste input + resultado + lead card.

### Request
```json
{
  "lead": {
    "owner_name": "Nombre Apellido",
    "owner_email": "owner@example.com",
    "owner_phone": "+34600111222",
    "consent_contact": true,
    "consent_text_version": "v1",
    "source_campaign": "meta_feb26",
    "utm_source": "meta",
    "utm_medium": "cpc",
    "utm_campaign": "iei_mvp",
    "utm_term": "vender piso",
    "utm_content": "ad_a"
  },
  "input": {
    "property": {
      "zone_key": "castelldefels",
      "municipality": "Castelldefels",
      "neighborhood": "Centro",
      "postal_code": "08860",
      "property_type": "piso",
      "m2": 90,
      "condition": "buen_estado",
      "year_built": 1998,
      "has_elevator": true,
      "has_terrace": true,
      "terrace_m2": 8,
      "has_parking": false,
      "has_views": false
    },
    "owner": {
      "sale_horizon": "3-6m",
      "motivation": "compra_otra",
      "already_listed": "no",
      "exclusivity": "depende",
      "expected_price": 380000
    }
  }
}
```

### Response 201
```json
{
  "lead_id": "34d6cfce-6222-4c31-8c9b-c21dc8b23c4e",
  "status": "nuevo",
  "result": {
    "iei_score": 63,
    "tier": "C"
  },
  "lead_card": {
    "iei_score": 63,
    "tier": "C"
  },
  "created_at": "2026-02-26T10:30:00Z"
}
```

### Errores
- 400 `CONSENT_REQUIRED` si `consent_contact=false`.
- 400 `VALIDATION_ERROR`.
- 422 `ZONE_NOT_CONFIGURED`.

## 5) GET `/api/admin/leads`
Lista leads con filtros.

### Query params
- `tier` (`A|B|C|D`)
- `zone_key`
- `sale_horizon`
- `status`
- `date_from`
- `date_to`
- `page`
- `page_size`

### Response 200 (ejemplo)
```json
{
  "items": [
    {
      "lead_id": "34d6cfce-6222-4c31-8c9b-c21dc8b23c4e",
      "created_at": "2026-02-26T10:30:00Z",
      "status": "nuevo",
      "tier": "C",
      "iei_score": 63,
      "zone_key": "castelldefels",
      "sale_horizon": "3-6m",
      "owner_name": "Nombre Apellido",
      "owner_phone": "+34600111222"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## 6) PATCH `/api/admin/leads/:id`
Actualiza estado comercial.

### Request
```json
{
  "status": "contactado"
}
```

### Response 200
```json
{
  "lead_id": "34d6cfce-6222-4c31-8c9b-c21dc8b23c4e",
  "status": "contactado",
  "updated_at": "2026-02-26T12:00:00Z"
}
```

## 7) GET `/api/admin/zones`
Lista configuracion de zonas.

### Response 200
```json
{
  "items": [
    {
      "zone_key": "castelldefels",
      "municipality": "Castelldefels",
      "base_per_m2": 3350,
      "demand_level": "alta",
      "type_factor_overrides": null,
      "condition_factor_overrides": null,
      "extras_add_overrides": null,
      "extras_cap_override": null,
      "is_active": true
    }
  ]
}
```

## 8) PATCH `/api/admin/zones/:id`
Actualiza configuracion de zona sin tocar codigo.

### Request
```json
{
  "base_per_m2": 3425,
  "demand_level": "media",
  "extras_cap_override": 0.1,
  "is_active": true
}
```

### Response 200
```json
{
  "zone_key": "castelldefels",
  "base_per_m2": 3425,
  "demand_level": "media",
  "updated_at": "2026-02-26T12:10:00Z"
}
```

## 9) Campos previstos v2 (backward compatible)

Los siguientes campos se documentan como opcionales para evolucion v2, manteniendo compatibilidad con contratos MVP.

### Campos opcionales previstos
1. `price_estimate.adjusted_price_raw`
2. `pricing_alignment.delta_raw`
3. `lead_card.data_quality_flags[]`
4. `lead_card.commercial_confidence` (0-1)
5. `lead_card.confidence_bucket`

### Estado actual
- El MVP actual no expone estos campos.
- Los contratos y respuestas actuales se mantienen sin cambios.
- Todos los campos anteriores deben tratarse como: `Campo previsto v2 (no expuesto en MVP)`.
