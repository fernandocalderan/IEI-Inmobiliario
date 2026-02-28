# COMPLIANCE - IEI Inmobiliario MVP

## 1) Consentimiento
- Checkbox obligatorio.
- Guardar `consent_text_version` y `consent_timestamp`.
- Sin consentimiento no se crea lead comercial.

## 2) Transparencia del modelo IEI™
- `IEI™` significa `Índice de Evaluación Integral`.
- Es un framework determinista basado en reglas.
- No es tasación oficial ni homologada.
- Determinismo no implica garantía de cierre o precio final.

## 3) Branding y finalidad
- IEI se presenta como tecnología (`Powered by IEI™`), no como marca comercial principal al propietario.
- El uso de la etiqueta tecnológica no modifica la finalidad del tratamiento de datos.

## 4) Seguridad y minimización
- `ip_hash` en servidor.
- minimizar PII en export por defecto (`EXPORT_PII=false`).
- canal de supresión (`/api/privacy/delete-request`).
