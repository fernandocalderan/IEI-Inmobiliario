# BUILD PLAN - IEI Inmobiliario MVP

## Fase 0 - Setup repo + config zonas

### Objetivos
- Estructura base frontend/backend/db.
- Cargar zonas iniciales y validar que motor responde.

### Entregables
1. Proyecto con modulos `frontend`, `api`, `db`, `docs`.
2. Seed de `zones` con 2-3 zonas piloto.
3. Smoke test `compute_iei` con casos de ejemplo.

### Checklist
- [ ] Motor importable desde API
- [ ] Zonas piloto activas en DB
- [ ] Error controlado para zona no configurada

## Fase 1 - Landing + formulario + scoring endpoint

### Objetivos
- Flujo completo hasta resultado IEI sin admin avanzado.

### Entregables
1. Landing neutra.
2. Formulario por pasos con validaciones.
3. `POST /api/iei/score` operativo.
4. Pantalla de resultado con rango + recomendacion.

### Checklist
- [ ] Campos formulario alineados 1:1 con `LeadInput`
- [ ] Tramos score/tier exactos del motor
- [ ] Tracking minimo (`view_landing`, `start_form`, `step_complete`, `view_result`)

## Fase 2 - Almacenamiento + admin basico + export lead card

### Objetivos
- Persistir leads y habilitar operacion comercial.

### Entregables
1. `POST /api/leads` con consentimiento obligatorio.
2. Tablas `leads`, `property_inputs`, `owner_signals`, `iei_results`, `zones`.
3. Admin basico: listado + filtros + cambio de estado.
4. Export de `lead_card` (JSON/CSV).

### Checklist
- [ ] Guardado transaccional de lead + resultado
- [ ] Filtros por tier/zona/horizonte
- [ ] Auditoria minima (`created_at`, `updated_at`, `utm`, `ip_hash`)

## Fase 3 - QA + hardening + medicion

### Objetivos
- Estabilizar calidad de dato, seguridad y conversion.

### Entregables
1. Suite de tests de reglas criticas.
2. Rate limiting y controles anti-spam.
3. Dashboard de metricas comerciales.
4. Protocolo operativo de revisiones de zona.

### Checklist
- [ ] Tests de tier y price alignment
- [ ] Monitoreo p95 endpoint scoring
- [ ] Metricas CPL, completion, %Tier A/B, coste por premium
- [ ] Flujo de supresion de datos operativo

## Epica: IEI Engine v2

### Tarea 1: `adjusted_price_raw`
Definition of Done:
- Se anade campo raw en salida tecnica del motor v2.
- No rompe campos actuales (`adjusted_price`, `range_low`, `range_high`).
- Contratos MVP siguen validos.

### Tarea 2: validacion `m2` + `data_quality_flags`
Definition of Done:
- Reglas de outlier definidas y documentadas.
- Flags de calidad generados de forma determinista.
- Casos de validacion cubiertos en tests.

### Tarea 3: factor antiguedad
Definition of Done:
- Impacto por `year_built` implementado con cap +/-2%.
- Casos borde documentados (sin `year_built`, extremos).
- Tests unitarios de factor completos.

### Tarea 4: ajuste scoring `already_listed`
Definition of Done:
- Nuevos pesos definidos con racional comercial.
- Backtest comparativo MVP vs v2 documentado.
- Sin regresiones en tiers para zonas piloto.

### Tarea 5: `commercial_confidence`
Definition of Done:
- Score de confianza definido en rango `0..1`.
- Regla separada del IEI Score comercial.
- Exposicion opcional en API y lead card v2.

### Tarea 6: backward compatibility API
Definition of Done:
- Campos v2 agregados como opcionales.
- Clientes MVP siguen operando sin cambios.
- Documentacion de compatibilidad actualizada.

### Tarea 7: tests unitarios
Definition of Done:
- Cobertura de nuevas reglas v2 (raw delta, flags, antiguedad, confidence).
- Tests de no regresion para reglas MVP existentes.
- CI en verde en ramas de release.

### Tarea 8: calibracion con agencias
Definition of Done:
- Dataset minimo de feedback comercial recolectado.
- Informe de calibracion por tier/zona.
- Ajustes priorizados para siguiente iteracion.

## Epica: Informe PDF Agencia (v2)

### Tarea 1: disenar plantilla HTML base
Definition of Done:
- Estructura visual cerrada con bloques de score, pricing y senales.
- Compatible con render server-side.
- Mantiene lenguaje comercial y tecnico coherente.

### Tarea 2: render server-side
Definition of Done:
- Pipeline de render reproducible en backend.
- Entradas del PDF definidas desde `lead_card` + metadatos.
- No altera logica del motor IEI.

### Tarea 3: exportacion PDF
Definition of Done:
- Generacion PDF consistente en entornos `staging/prod`.
- Control de errores y reintento basico documentado.
- Salida con formato estable para uso comercial.

### Tarea 4: versionado por timestamp
Definition of Done:
- Cada informe guarda timestamp/version en metadatos.
- Trazabilidad de cambios de contenido.
- Convencion de nombres definida para almacenamiento.

### Tarea 5: watermark dinamico (si confidence < 0.65)
Definition of Done:
- Watermark activado para `low/unreliable` confidence.
- Regla de umbral documentada y testeable.
- No modifica score ni tier calculados.

### Definition of Done global epica PDF
- PDF reproducible.
- No altera logica del motor.
- Incluye disclaimers de compliance.

## Epica: Comercializacion IEI (v2)

### Subtarea 1: implementar `commercial_confidence`
Definition of Done:
- Formula determinista documentada y validada en test.
- Buckets `high|medium|low|unreliable` definidos.
- Separacion clara respecto a IEI Score.

### Subtarea 2: anadir campos backward compatible
Definition of Done:
- Campos v2 agregados como opcionales.
- Clientes MVP no requieren cambios.
- Contratos versionados y documentados.

### Subtarea 3: activar pricing dinamico
Definition of Done:
- Multiplicadores por confidence aplicables por regla.
- Tabla de precios por tier versionada.
- Politica de no venta para `unreliable` definida.

### Subtarea 4: disenar PDF Agencia
Definition of Done:
- Blueprint implementable aprobado por negocio.
- Estructura alineada con PRD.
- Disclaimers incluidos.

### Subtarea 5: calibracion con 2 agencias piloto
Definition of Done:
- Dos pilotos activos con tracking de resultados.
- Feedback comercial consolidado.
- Ajustes priorizados para iteracion siguiente.

### Subtarea 6: medicion de separacion estadistica por tier
Definition of Done:
- Metricas de separacion definidas (cita, exclusiva, cierre).
- Reporte por zona/tier con lectura accionable.
- Criterios de exito/fracaso acordados.

## Epica: Refinamientos pre-mercado (V2)

Formalizacion para refinamientos pre-mercado (v2), sin implementacion en el motor MVP actual.

### Tareas

1. **Documentar y validar requisitos de validacion de datos**
- Reglas de `m2`, `expected_price`, `zone_key`.
- `data_quality_flags`.
- DoD: flags documentados + ejemplos.

2. **Ajustar especificacion de scoring comercial**
- Revision de tramos de price alignment.
- Separacion explicita IEI Score vs Confidence.
- DoD: documento con tramos + casos de prueba.

3. **Definir metricas de pilotaje y dashboard**
- Metricas por flag y bucket.
- DoD: especificacion de eventos y slices.

4. **Disenar pipeline de datos de pricing por zona**
- Versionado trimestral.
- DoD: JSON de base prices con tagging de periodo.

5. **QA de documentacion cruzada**
- Revisar coherencia TECHSPEC ↔ ANALYTICS ↔ API ↔ DATA_MODEL.
- DoD: fixture de validacion/ejemplo.

6. **Stress test + simulacion de distribucion IEI**
- Script reproducible.
- CSV export.
- Reporte por tier.
- Tests minimos en CI local.

## Checklist salida a produccion
- [ ] Contratos API congelados y versionados
- [ ] Consentimiento legal validado
- [ ] Politica de retencion publicada
- [ ] Runbook de incidentes y rollback
- [ ] Backups DB y prueba de restauracion
- [ ] QA E2E en `staging`
