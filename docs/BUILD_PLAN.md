# BUILD PLAN - IEI Inmobiliario MVP

## Fase 0
- Setup repo/API/DB/frontend.
- Seed zonas.

## Fase 1
- Landing + wizard + score endpoint.

## Fase 2
- Persistencia lead + admin + operación comercial (reserve/release/sell/export).

## Fase 3
- QA + hardening + métricas.

## Épica: Premium pricing + A+
- policy por zona
- segmentación A+
- persistencia `lead_price_eur` y `pricing_policy`

## Épica: Rebrand IEI Framework (docs + metadata + UI)
### Tareas
1. Definir estándar global de naming IEI™.
2. Añadir metadata `iei_framework` opcional en `/api/iei/score` y `/api/leads`.
3. Incluir metadata en `lead_card_json` y export comercial.
4. Ajustar frontend owner-facing a `Powered by IEI™` en bloque de confianza.
5. Ajustar admin con etiqueta `IEI™ Framework v1.0`.
6. Publicar `IEI_FRAMEWORK.md` e `IEI_MANIFESTO.md`.

### DoD
- Sin cambios en scoring ni contratos core.
- Campos nuevos opcionales y backward compatible.
- No referencias a significados anteriores de IEI.
