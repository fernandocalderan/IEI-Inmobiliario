# TECHSPEC - Informe de Ventabilidad Inmobiliaria (MVP)

## 1) Arquitectura propuesta

### Componentes
1. Frontend web
- Landing + formulario por pasos + pantalla resultado.
- Consume API REST.

2. API backend
- Validacion de input.
- Orquestacion de scoring (`compute_iei`).
- Persistencia de lead y resultados.
- Endpoints admin.

3. Motor IEI (modulo)
- Archivo fuente: `iei_engine.py`.
- Uso como dependencia interna determinista.

4. Base de datos
- Leads, inputs, resultados IEI, configuracion de zonas, auditoria.

5. Admin
- Lista/filtrado de leads.
- Cambio de estado.
- Edicion de config por zona.

## 1.1) Contratos del motor (fuente unica)

1. Inputs
- `PropertyFeatures`:
  `zone_key`, `municipality`, `neighborhood`, `postal_code`, `property_type`, `m2`, `condition`, `year_built`, `has_elevator`, `has_terrace`, `terrace_m2`, `has_parking`, `has_views`.
- `OwnerSignals`:
  `sale_horizon`, `motivation`, `already_listed`, `exclusivity`, `expected_price`.
- `LeadInput`:
  `property: PropertyFeatures`, `owner: OwnerSignals`.

2. Outputs
- `PriceEstimate`:
  `base_per_m2`, `base_price`, `adjusted_price`, `range_low`, `range_high`, `demand_level`, `applied_factors`.
- `IEIResult`:
  `iei_score`, `tier`, `breakdown`, `price_estimate`, `pricing_alignment`, `recommendation`.
- `lead_card(lead, result)`:
  objeto con bloques `zone`, `property`, `pricing`, `owner_signals`, ademas de score/tier y recomendacion.

## 2) Responsabilidades por componente

1. Frontend
- Recolectar campos exactos del motor.
- Validaciones basicas UX (tipos, required, rangos).
- Mostrar resultado y consentimiento.

2. API
- Validacion estricta de enums y campos.
- Normalizacion (`zone_key.lower().strip()`).
- Manejo de errores del motor (zona no configurada).
- Persistencia transaccional de lead + resultado.

3. Motor
- Calculo de precio (`estimate_price`).
- Calculo score/tier/recomendacion (`compute_iei`).
- Render de `lead_card`.

4. Admin
- Supervisar calidad de leads.
- Ajustar zonas sin editar codigo.

## 3) Integracion del motor como modulo

### Estrategia
- Import directo del modulo:
```python
from iei_engine import LeadInput, PropertyFeatures, OwnerSignals, compute_iei, lead_card
```

### Reglas
- Tratar `iei_engine.py` como fuente unica de logica.
- Evitar duplicar reglas de scoring en API.
- Toda transformacion debe ser de mapping/validacion, no de negocio.

### Versionado recomendado
- Opcion A (MVP): version fija en repo (`iei_engine.py`) + changelog manual.
- Opcion B: encapsular en paquete interno (`iei_engine`), con semver.

### Tests minimos obligatorios
1. Test de contrato de entrada/salida (`LeadInput` -> `IEIResult`).
2. Test de tramos de `_price_alignment_score`.
3. Test tiers (`85`, `70`, `55`, `54`).
4. Test error por zona no configurada.
5. Test cap de extras en `EXTRAS_CAP`.

## 4) Configuracion por zona sin tocar codigo

### Objetivo
Permitir actualizar `base_per_m2`, demanda y overrides mediante datos en DB/admin.

### Modelo operativo MVP
1. Tabla `zones` como fuente editable por admin.
2. Carga en memoria con cache corto (ej. 5 min).
3. Adaptador en API que construya tablas runtime para el motor.

### Reglas
- Zona activa solo si tiene `base_per_m2` y `demand_level` validos.
- Si falta config en runtime: responder error controlado equivalente a "zona no configurada".
- Se recomienda versionar `base_per_m2` por trimestre (ej: `2026Q1`) para trazabilidad historica.

### Campos minimos de zona
- `zone_key` (unique)
- `municipality`
- `base_per_m2`
- `demand_level` (`alta|media|baja`)
- Overrides opcionales (`type_factor`, `condition_factor`, `extras_add`, `extras_cap`)

## 4.1) Limitaciones actuales del modelo (MVP)

1. _price_alignment_score() utiliza adjusted_price ya redondeado como referencia de cálculo de delta, lo que puede generar saltos artificiales en los tramos de scoring cuando el gap está cercano a los umbrales definidos (5%, 10%, 15%, 25%).
2. No existe validacion estricta de `m2`; outliers no estan controlados desde el motor.
3. `year_built` no impacta hoy ni en precio ni en score.
4. La penalizacion por `already_listed` es leve dentro de `_intention_score`.
5. `BASE_PRICE_PER_M2` y `DEMAND_INDEX` son tablas estaticas y requieren versionado para historico.

## 4.2) Evolucion prevista - IEI Engine v2 (sin implementacion actual)

1. Anadir `adjusted_price_raw` a `PriceEstimate`.
2. Calcular `delta` de pricing alignment usando solo valor raw.
3. Incorporar `data_quality_flags` para identificar calidad/consistencia del input.
4. Introducir `commercial_confidence` (0-1) como indicador de confiabilidad comercial.
5. Incorporar factor de antiguedad capado en +/-2%.
6. Revisar scoring de `already_listed` para diferenciar mejor oportunidad caliente vs competitiva.
7. Separar explicitamente score comercial (ventabilidad) de calidad de dato.

## 4.3) Commercial Confidence (v2 - especificacion tecnica)

### Definicion
- `commercial_confidence` (0-1) mide calidad y completitud del input.
- No mide intencion de venta ni reemplaza el IEI Score.
- Estado: campo previsto v2, no implementado en MVP actual.

### Formula propuesta (determinista)
1. Base = `1.0`
2. Penalizaciones:
- `expected_price is None` -> `-0.20`
- `m2 <= 0` -> `-0.50`
- `m2 < 20 or m2 > 500` -> `-0.15`
- `zone not versioned` -> `-0.10`
- `property_type missing` (si aplicable) -> `-0.15`
3. Confidence final:
- `confidence = clamp(base - penalizaciones, 0, 1)`
Nota: las penalizaciones son acumulativas (se suman entre sí).

### Buckets operativos
- `0.85-1.00`: High Confidence
- `0.65-0.84`: Medium
- `0.40-0.64`: Low
- `<0.40`: Unreliable

### Consideraciones de integracion
- Debe calcularse de forma independiente al scoring IEI.
- Debe exponerse como dato opcional v2 en `lead_card`.
- Debe conservar compatibilidad con contratos MVP actuales.

### 5) Validacion de inputs (pre-scoring)

Formalizacion para refinamientos pre-mercado (v2), sin cambios sobre contratos MVP actuales.

#### Reglas de validacion (estrictas)
- **m2**
  - Si `m2 <= 0`: marcar `M2_INVALID`
  - Si `m2 < 20` o `m2 > 500`: marcar `M2_OUTLIER`
- **expected_price**
  - Si `expected_price` esta ausente o `<= 0`: marcar `MISSING_EXPECTED_PRICE`
- **zone_key**
  - Si `zone_key` no esta en tablas: marcar `ZONE_UNKNOWN`

#### Flags de calidad (documentacion)
Los flags anteriores se agrupan bajo:

```text
data_quality_flags: [
  "M2_INVALID",
  "M2_OUTLIER",
  "MISSING_EXPECTED_PRICE",
  "ZONE_UNKNOWN"
]
```

Estos flags no afectan el scoring del MVP, pero se usan para documentacion del lead y metricas de confianza.

### 6) Scoring refinado y alineacion de precio

Formalizacion para refinamientos pre-mercado (v2), sin implementacion en el motor MVP.

Para mejorar precision antes de pilotaje, se recomienda documentar:

**Price alignment scoring tramos detallados:**

| Gap % vs ref | Score |
|--------------|-------|
| gap < -10% | 20 |
| <= +5% | 30 |
| +5% < gap <= +10% | 22 |
| +10% < gap <= +15% | 14 |
| +15% < gap <= +25% | 6 |
| > +25% | 0 |

**Notas detalladas:**
- `ref` debe ser siempre `adjusted_price_raw` (sin redondeo).
- Rango conservador (-3/+5) se usa para display, no para calculo interno de delta.

### 7) Score vs Confidence

Formalizacion para refinamientos pre-mercado (v2), sin cambios de contrato MVP.

El IEI Score evalua oportunidad; `commercial_confidence` evalua calidad del dato.

Para pilotaje y pricing:
- Solo leads con `commercial_confidence >= 0.65` y Tier A/B deben considerarse como candidatas a pricing premium.
- Leads con `commercial_confidence < 0.40` se excluyen del piloto de venta.
- Leads con flags M2_INVALID o ZONE_UNKNOWN deben excluirse automaticamente del piloto comercial.

## 5) Requisitos no funcionales

1. Latencia
- `POST /api/iei/score` p95 < 300 ms (sin dependencias externas).

2. Disponibilidad
- Objetivo MVP >= 99.5% mensual.

3. Logging
- Log estructurado por request_id.
- Log de errores de validacion y zona.
- No loggear datos sensibles en claro.

4. Seguridad
- TLS obligatorio.
- Rate limiting por IP y por fingerprint.
- Hardening de admin (auth + roles).
- Hash de IP (`ip_hash`) para auditoria minimizada.

5. Integridad de datos
- Escrituras transaccionales para lead + resultado.
- Timestamps UTC.

6. Observabilidad
- Metricas API, conversion embudo, calidad de leads.

## 6) Manejo de errores tecnico

### Casos
1. Zona no configurada
- HTTP 422
- `code: ZONE_NOT_CONFIGURED`

2. Input invalido
- HTTP 400
- detalle por campo

3. Consentimiento no otorgado en creacion lead
- HTTP 400 o 409 segun politica
- `code: CONSENT_REQUIRED`

## 7) Despliegue MVP

1. Entornos
- `dev`, `staging`, `prod`

2. Variables de entorno
- Conexion DB
- Secretos auth admin
- Parametros de rate limiting

3. Rollback
- Revert de release API/UI.
- Restaurar snapshot DB si aplica.
- Regenerar docs/contratos desde `iei_engine.py` si hay desalineacion.

## 8) Metricas de calibracion del modelo

### Objetivos
1. Tier A >= 2x tasa de cita vs Tier B.
2. 40-60% de expectativas dentro del rango estimado.
3. Correlacion de `gap_percent > 15%` con menor tasa de cierre.
4. Segmentacion obligatoria por `zone_key`, `property_type`, `tier` y `already_listed`.
5. Separacion estadistica clara entre tiers: el Tier A debe mostrar diferencia significativa en tasa de cita y cierre frente a Tier B y C.

### Eventos minimos de calibracion
1. `lead_scored`
2. `lead_contacted`
3. `appointment_set`
4. `exclusive_signed`
5. `sale_closed`
