# PRD - Informe de Ventabilidad Inmobiliaria (MVP + Premium)

## 1) Producto
El producto capta propietarios, evalúa ventabilidad y entrega leads comercialmente accionables a agencias.

Marca visible al propietario:
- Producto: Informe de Ventabilidad.
- Tecnología: `Powered by IEI™`.

Definición oficial de tecnología:
- `IEI™ — Índice de Evaluación Integral`.
- Framework propietario de evaluación determinista, versionado y auditable.

## 2) Usuarios
1. Propietario
- Recibe rango conservador y recomendación.
- No ve pricing B2B del lead.

2. Agencia
- Recibe score/tier, señales, gap, estado comercial.
- Recibe metadatos premium: `segment`, `lead_price_eur`, `pricing_policy`.

## 3) Flujo
1. Landing.
2. Wizard 4 pasos.
3. `POST /api/iei/score`.
4. Captura contacto + consentimiento.
5. `POST /api/leads`.
6. Admin: reservar, vender, exportar.

## 4) Tecnología IEI™
En resultados y piezas de confianza debe mostrarse:
- `Powered by IEI™ — Índice de Evaluación Integral`.
- Nota legal: modelo determinista basado en reglas; no es tasación oficial.

IEI no se usa como marca comercial principal frente al propietario.

## 5) Reglas comerciales
### Tier del motor
- A `>=85`
- B `70-84`
- C `55-69`
- D `<55`

### Policy premium Baix Llobregat
- `A_PLUS=150`, `A=90`, `B=55`, `C=25`, `D=0`.
- Segmento `A_PLUS` basado en reglas de salida del motor (sin tocar scoring core).

## 6) Resultado esperado
- Operación comercial sin doble venta ni duplicados.
- Monetización por tier/segment/policy.
- Trazabilidad técnica y narrativa coherente de IEI™ como framework propietario.
