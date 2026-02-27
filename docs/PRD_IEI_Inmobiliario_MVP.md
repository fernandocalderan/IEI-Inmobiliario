# PRD - Informe de Ventabilidad Inmobiliaria (MVP neutro)

## 1) Resumen del producto (1 pagina)

### Nombre
Informe de Ventabilidad Inmobiliaria (MVP neutro)

### Problema
- Propietarios no tienen referencia clara y conservadora de precio de venta realista.
- Inmobiliarias reciben leads con calidad heterogenea y baja trazabilidad de intencion real.

### Solucion MVP
- Captar propietario con landing neutra.
- Recoger datos exactos del inmueble + senales del propietario (campos del motor IEI).
- Ejecutar motor determinista `iei_engine.py` para:
1. Estimar rango de precio conservador.
2. Calcular IEI Score (0-100).
3. Clasificar Tier (A/B/C/D).
4. Construir `lead_card` accionable para inmobiliaria.

### Propuesta de valor
- Para propietario: orientacion inmediata de rango de venta y recomendacion accionable.
- Para inmobiliaria: lead priorizado por probabilidad de captacion y vendibilidad.

### Objetivo de negocio
- Convertir trafico en leads cualificados.
- Monetizar leads premium (Tier A/B).

### No objetivos MVP
- No automatizar firma de encargo.
- No usar modelos ML ni fuentes externas en tiempo real.
- No sustitucion de tasacion homologada.

## 2) Usuario 1: Propietario

### Motivacion
- Saber "cuanto podria vender" con criterio realista.
- Entender si su expectativa esta alineada con mercado.

### Valor inmediato
- Rango estimado: `range_low` - `range_high`.
- Centro estimado: `adjusted_price`.
- Nota de alineacion de precio (`pricing_alignment.note`).
- Recomendacion de accion (`recommendation`).

### Outputs visibles
- Score IEI (puede mostrarse resumido o completo).
- Tier interno (opcional de cara a usuario final, obligatorio en admin).
- Mensaje de recomendacion.

## 3) Usuario 2: Inmobiliaria

### Que recibe
- `lead_card` completo con:
1. `iei_score`, `tier`, `breakdown`.
2. Zona y demanda (`demand_level`).
3. Datos de inmueble y extras.
4. Rango estimado, expectativa del propietario y `gap_percent`.
5. Senales de intencion (`sale_horizon`, `motivation`, `already_listed`, `exclusivity`).
6. Recomendacion operativa.

### Por que paga
- Priorizacion comercial por tiers.
- Menor tiempo en leads frios.
- Mejor tasa de contacto, cita y captacion en leads premium.

## 4) Flujo end-to-end

1. Captacion
- Landing neutra con CTA a formulario.

2. Formulario (pasos)
- Paso inmueble (`PropertyFeatures`).
- Paso intencion (`OwnerSignals` sin expectativa).
- Paso precio esperado (`expected_price`, opcional).
- Paso datos de contacto + consentimiento.

3. Scoring
- API ejecuta `compute_iei(LeadInput)`.
- Si zona no configurada: error bloqueante.

4. Resultado propietario
- Mostrar rango, nota de alineacion y recomendacion.
- Solicitar/confirmar datos para compartir con inmobiliarias.

5. Entrega lead
- Persistir lead + input + resultado + `lead_card`.
- Inmobiliaria consume vista admin filtrando Tier A/B.

## 5) Definicion de lead premium (Tier A/B)

### Reglas exactas de tier
- Tier A: `iei_score >= 85`
- Tier B: `70 <= iei_score <= 84`
- Tier C: `55 <= iei_score <= 69`
- Tier D: `iei_score < 55`

### Definicion comercial MVP
- Lead premium: Tier A o Tier B.
- Recomendacion comercial:
1. Tier A: contacto prioritario inmediato.
2. Tier B: contacto en ventana corta y trabajo de ajuste de precio/presentacion.

## 5.1) Calidad del Lead y Confianza (v2)

En la evolucion v2, el producto mostrara de forma clara:
- IEI Score (0-100)
- Tier (A-D)
- Rango estimado
- Gap vs expectativa (`gap_percent`)
- `commercial_confidence` (v2) como indicador de calidad del dato

Regla de producto:
- `commercial_confidence` no reemplaza el IEI Score.
- El score mantiene la prioridad comercial.
- La confidence ayuda a interpretar la fiabilidad del input y del resultado.

## 5.2) Modelo de monetizacion por Tier y Confidence (v2)

### Base pricing sugerido (ejemplo MVP comercial)
| Tier | Base EUR |
|---|---|
| A | 45-70 EUR |
| B | 25-40 EUR |
| C | 10-20 EUR |
| D | No vendible / remarketing |

### Ajuste por Confidence
- High -> `+20%`
- Medium -> base
- Low -> `-20%`
- Unreliable -> no vendible

### Formula ejemplo
- `lead_price = tier_base_price * confidence_multiplier`

### Reglas comerciales
1. Leads `Tier A + High Confidence` = segmento premium.
2. Leads `Tier C/D` = venta bajo suscripcion o estrategia de nurturing.
3. Estado: modelo previsto para v2, no activado en MVP actual.

## 5.3) Informe IEI - Version Agencia (Blueprint v2)

### Objetivo
Documento comercial explicativo para justificar:
- IEI Score
- Tier
- Rango estimado
- Gap vs expectativa
- Recomendacion estrategica

### Estructura PDF
1. Portada
- Logo IEI
- Fecha
- Zona
- IEI Score + Tier

2. Resumen Ejecutivo
- Ventabilidad estimada
- Rango de precio estimado
- Nivel de demanda de la zona

3. Analisis de Precio
- Precio esperado vs estimado
- Gap %
- Nota tecnica

4. Senales del Propietario
- Horizonte
- Motivacion
- Exclusividad

5. Recomendacion
- Estrategia sugerida

6. Nota metodologica
- Modelo determinista basado en reglas
- No es tasacion oficial

### Estado
- Blueprint de producto v2, no implementado en MVP actual.

## 6) Reglas y tramos del motor (fuente unica)

### 6.1 Puntuacion intencion (0-40)
`_intention_score(owner)` suma:

1. Horizonte de venta
- `<3m`: 18
- `3-6m`: 14
- `6-12m`: 8
- `valorando`: 0

2. Motivacion
- `traslado`, `herencia`, `divorcio`, `finanzas`: 10
- `mejora`, `compra_otra`: 7
- `inversion`, `otro`: 4
- `curiosidad`: 0

3. Ya listado
- `no`: 4
- `si_con_agencia`: 2
- `si_por_su_cuenta`: 3

4. Disposicion a exclusiva
- `si`: 8
- `depende`: 4
- `no`: 0

Resultado con clamp `0..40`.

### 6.2 Puntuacion alineacion precio (0-30)
`_price_alignment_score(expected_price, est)`:

1. Sin expectativa (`None` o `<=0`)
- score = 10
- nota: alineacion parcial por menor precision comercial.

2. Con expectativa
- Referencia: `est.adjusted_price`
- `delta = (expected_price - adjusted_price) / adjusted_price`

Tramos:
- `delta <= 0.05`: 30
- `delta <= 0.10`: 22
- `delta <= 0.15`: 14
- `delta <= 0.25`: 6
- `delta > 0.25`: 0

Regla adicional:
- Si `delta < -0.10`, score forzado a 20.

`gap_percent = round(delta*100, 1)`.

### 6.3 Puntuacion mercado (0-30)
`_market_score(property, estimate)` suma:

1. Demanda zona (`_demand_points`)
- alta: 12
- media: 8
- baja: 4

2. Tipologia (`_type_points`)
- piso: 8
- atico: 10
- casa_adosada: 10
- chalet: 10
- planta_baja: 5

3. Estado (`_condition_points`)
- reformado: 8
- buen_estado: 6
- a_reformar_parcial: 3
- a_reformar_integral: 2

4. Extras (`_extras_points`)
- +1 por elevator, parking, terrace, views
- cap maximo: 4 puntos

Resultado con clamp `0..30`.

### 6.4 Score total
- `iei_score = clamp(intencion + precio + mercado, 0..100)`

## 7) Asunciones MVP del precio estimado

### Tablas configurables
- `BASE_PRICE_PER_M2`
- `DEMAND_INDEX`
- `TYPE_FACTOR`
- `CONDITION_FACTOR`
- `EXTRAS_ADD`
- `EXTRAS_CAP`

### Valores actuales del motor (MVP)
1. `BASE_PRICE_PER_M2`
- `castelldefels`: 3350.0
- `gava`: 3100.0
- `sitges`: 4100.0

2. `DEMAND_INDEX`
- `castelldefels`: `alta`
- `gava`: `media`
- `sitges`: `alta`

Nota:
- Si falta demanda para una zona existente, el motor usa `media` por defecto (`DEMAND_INDEX.get(zone, DemandLevel.MEDIA)`).

3. `TYPE_FACTOR`
- `piso`: 1.00
- `atico`: 1.08
- `planta_baja`: 0.93
- `casa_adosada`: 1.05
- `chalet`: 1.12

4. `CONDITION_FACTOR`
- `reformado`: 1.08
- `buen_estado`: 1.00
- `a_reformar_parcial`: 0.92
- `a_reformar_integral`: 0.85

5. `EXTRAS_ADD`
- `elevator`: +0.04
- `terrace_big` (>10 m2): +0.03
- `terrace_small` (<=10 m2 o sin dato): +0.02
- `parking`: +0.04
- `views`: +0.06

6. `EXTRAS_CAP`
- 0.10 (maximo +10% acumulado)

### Formula
1. `base_price = m2 * base_per_m2`
2. `adjusted = base_price * type_factor * condition_factor * extras_factor`
3. `extras_factor = 1 + clamp(sum(extras), 0, EXTRAS_CAP)`

### Rango conservador y asimetrico
- `low = adjusted * 0.97` (-3%)
- `high = adjusted * 1.05` (+5%)

### Redondeo
- `_round_price`: multiplo de 500 EUR.

### Cap extras
- acumulado maximo +10% (`EXTRAS_CAP = 0.10`).

## 8) Casos limite

1. Sin expectativa de precio
- No bloquea.
- Score precio fijo = 10.

2. Zona sin configuracion
- `estimate_price` lanza `ValueError("Zona no configurada: ...")`.
- Debe mostrarse mensaje controlado y no guardar score parcial.

3. `m2` invalido (0 o negativo)
- El motor no valida explicitamente.
- API/UI MVP debe validar `m2 > 0` antes de ejecutar motor.

4. `expected_price <= 0`
- Se trata como "sin expectativa".

5. `has_terrace=true` con `terrace_m2` vacio
- Aplica `terrace_small` (+2%).

6. Extras excesivos
- Aplican sumatorio con cap (+10%).

## 9) Riesgos y mitigaciones

1. Sobrevaloracion percibida -> perdida de confianza
- Mantener rango conservador asimetrico (-3%/+5%).
- Mensaje claro: estimacion orientativa, no tasacion oficial.

2. Datos de zona insuficientes -> rangos pobres
- Activar zona solo con config cargada (`BASE_PRICE_PER_M2`, `DEMAND_INDEX`).
- Revisiones periodicas de tabla por operaciones.

3. Leads basura/fraude/spam
- Campos minimos obligatorios.
- Rate limiting y validaciones server-side.
- Opcional: verificacion telefono/OTP.

4. Desconfianza por contacto comercial
- Consentimiento explicito y granular.
- Transparencia sobre finalidad y cesion a inmobiliarias.

## 10) Criterios de exito MVP

- Completion rate formulario.
- % leads Tier A/B.
- Coste por lead premium.
- Tasa de contacto y tasa de cita de leads premium.
