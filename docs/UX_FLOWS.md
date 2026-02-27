# UX FLOWS - IEI Inmobiliario MVP

## 1) Landing neutra

### Objetivo
Convertir trafico frio en inicio de formulario.

### Secciones
1. Hero
- Titulo: "Recibe un informe orientativo de ventabilidad de tu inmueble".
- Subtitulo: "Rango realista + nivel de demanda + recomendacion".
- CTA: "Empezar informe".

2. Como funciona (3 pasos)
- Completa datos del inmueble.
- Indica tu momento de venta.
- Recibe tu rango orientativo.

3. Confianza
- Mensaje legal corto: "No es tasacion oficial".
- Tiempo estimado: 2-4 minutos.

4. FAQ breve
- Para que sirve.
- Quien puede contactar.

## 2) Formulario por pasos

### Paso 1: Inmueble (`PropertyFeatures`)
Campos:
- `zone_key`
- `municipality`
- `neighborhood` (opcional)
- `postal_code` (opcional)
- `property_type`
- `m2`
- `condition`
- `year_built` (opcional)
- `has_elevator`
- `has_terrace`
- `terrace_m2` (si `has_terrace=true`, opcional)
- `has_parking`
- `has_views`

Validaciones:
- `zone_key` obligatorio.
- `m2 > 0`.
- enums validos.

### Paso 2: Intencion (`OwnerSignals` parcial)
- `sale_horizon`
- `motivation`
- `already_listed`
- `exclusivity`

### Paso 3: Precio esperado
- `expected_price` opcional.
- Helper copy: "Si no lo sabes, puedes dejarlo vacio".

### Paso 4: Captura datos y consentimiento
- `owner_name`, `owner_email`, `owner_phone`.
- Checkbox obligatorio `consent_contact`.
- Enlace a politica de privacidad.

## 3) Pantalla de resultado

### Antes de captura de datos (si se usa gate)
- Vista parcial: rango estimado resumido y CTA "Desbloquear informe completo".

### Despues de captura de datos
Mostrar:
- `range_low` - `range_high`
- `adjusted_price` (precio centro)
- Nota de alineacion (`pricing_alignment.note`)
- Recomendacion (`recommendation`)
- Mensaje de siguiente paso (contacto por inmobiliaria colaboradora)

### Estados de error
1. Zona no configurada
- Mensaje: "Todavia no tenemos datos suficientes para esta zona".
- CTA: "Avisarme cuando este disponible".

2. Validacion de formulario
- Error por campo con texto claro.

## 4) Vista admin - Lead card

### Listado
- Columnas: fecha, estado, tier, score, zona, horizonte, contacto.
- Filtros: tier, zona, horizonte, estado, fechas.

### Detalle lead card
Bloques:
1. Score
- `iei_score`, `tier`, `breakdown`.

2. Zona y demanda
- `zone_key`, `municipality`, `neighborhood`, `postal_code`, `demand_level`.

3. Inmueble
- tipologia, m2, estado, ano, extras.

4. Precio
- rango estimado, centro, expectativa, gap %, nota.

5. Senales propietario
- horizonte, motivacion, estado de anuncio, exclusiva.

6. Recomendacion
- texto accionable del motor.
