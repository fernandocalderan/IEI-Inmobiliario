# TECHSPEC - IEI Inmobiliario MVP

## 1) Principio de arquitectura
- El motor (`iei_engine.py`) define score/tier/recomendación.
- La API añade capas comerciales y de presentación (pricing, reservas, metadata), sin alterar reglas core.

## 2) Definición framework
- `IEI™ — Índice de Evaluación Integral`
- Descriptor: framework propietario de evaluación determinista, versionado y auditable.
- Firma pública: `Powered by IEI™`.

## 3) Contratos del motor (intactos)
Inputs:
- `PropertyFeatures`, `OwnerSignals`, `LeadInput`

Outputs:
- `PriceEstimate`, `IEIResult`, `lead_card`

## 4) Metadata IEI (backward compatible)
Se añade metadata opcional en capa API, sin romper clientes existentes:

- `iei_framework.name = "IEI™"`
- `iei_framework.full_name = "IEI™ — Índice de Evaluación Integral"`
- `iei_framework.tagline = "Framework propietario de evaluación determinista, versionado y auditable."`
- `iei_framework.version = "1.0"`

Feature flag:
- `IEI_FRAMEWORK_ENABLED=true|false`

## 5) Superficies impactadas
1. `/api/iei/score`
- añade `iei_framework` opcional.

2. `/api/leads`
- añade `iei_framework` opcional.
- `lead_card` de respuesta incluye `iei_framework` y `powered_by`.

3. Persistencia
- `lead_card_json` guarda `iei_framework` y `powered_by`.
- No requiere migración al ya existir `lead_card_json`.

4. Export CSV ventas
- añade `iei_framework_version` y `powered_by`.

## 6) Versionado
- `engine_version`: versión del motor IEI de scoring.
- `framework_version`: versión de narrativa/framework IEI™ (`1.0`).

Separación explícita:
- cambiar framework_version no implica cambiar scoring.

## 7) Requisitos de UI
- Owner-facing: IEI solo como credencial en bloque confianza/footer.
- Admin-facing: mostrar `IEI™ Framework v1.0` + tooltip explicativo.

## 8) No cambios funcionales
- No se modifica `iei_engine.py`.
- No se cambian requests ni claves históricas (`iei_score`, `tier`, etc.).
- Los campos nuevos son opcionales y aditivos.
