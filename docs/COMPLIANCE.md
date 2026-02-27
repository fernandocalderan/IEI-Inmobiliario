# COMPLIANCE - IEI Inmobiliario MVP

## 1) Consentimiento de contacto (MVP)

### Checkbox obligatorio
Texto recomendado:
"Acepto que mis datos sean tratados para elaborar mi informe de ventabilidad y para que inmobiliarias colaboradoras puedan contactarme en relacion con la posible venta de mi inmueble."

### Reglas
- Checkbox desmarcado por defecto.
- Sin consentimiento no se crea lead comercial.
- Guardar `consent_text_version` y `consent_timestamp`.

## 2) Finalidad y minimizacion
- Finalidad primaria: generar informe orientativo.
- Finalidad secundaria: contacto comercial por inmobiliarias colaboradoras (solo con consentimiento).
- Minimizar datos: recoger solo lo necesario para scoring y contacto.

## 3) Conservacion de datos (nivel MVP)
- Leads no contactados: retencion sugerida 6-12 meses.
- Leads gestionados: retencion segun obligacion legal/comercial aplicable.
- Definir politica escrita y visible en privacidad.

## 4) Derecho de supresion (nivel MVP)
- Canal visible (email o formulario) para solicitar borrado.
- SLA interno recomendado: <= 30 dias naturales.
- Registrar fecha y resultado de solicitud.

## 5) Seguridad y acceso
- Acceso admin con autenticacion.
- Control de rol para visualizar datos de contacto.
- Cifrado en transito (TLS).
- Hash de IP en lugar de IP en claro (`ip_hash`).

## 6) Recomendaciones opcionales
1. Doble opt-in email para mejorar prueba de consentimiento.
2. Verificacion telefono (OTP) para reducir leads basura.
3. Registro de auditoria de cambios de estado de lead.

## 7) Nota legal
- Informe IEI es orientativo y no sustituye tasacion homologada.

## 8) Transparencia del modelo

1. El score IEI es determinista y basado en reglas explicitas.
2. El rango estimado esta disenado con enfoque conservador.
3. El informe no equivale a tasacion oficial.
4. Las tablas de zona deben versionarse para trazabilidad historica.
5. El resultado no garantiza cierre ni precio final de venta.

## 9) Transparencia comercial del informe

1. El IEI es un modelo determinista basado en reglas configurables.
2. No es una tasacion homologada ni sustituye informe oficial de tasacion.
3. `commercial_confidence` no implica probabilidad de cierre garantizada.
4. El rango publicado es una estimacion conservadora, no compromiso de precio final.
5. Todo material comercial debe incluir estos disclaimers de forma visible (v2).

## Mensajes de transparencia para pilotaje

Formalizacion para refinamientos pre-mercado (v2), sin cambios en contratos MVP actuales.

- El modelo es determinista y no una tasacion oficial.
- La estimacion de precio es conservadora.
- Flags de calidad seran visibles en lead card.
- Confidence no garantiza exito de venta.
