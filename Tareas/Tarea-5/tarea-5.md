# 📘 Día 5 — ETL: importar Excels sucios al ORM

---

## 🛠️ Antes de empezar: qué vamos a hacer

Hoy vas a recibir 3 archivos Excel reales con datos del fundo y vas a escribir comandos de Django que los importen a la base de datos. Los archivos vienen con todos los problemas que tienen los Excels en producción: hojas múltiples con encabezados falsos, columnas en orden distinto según el día, RUTs en 6 formatos diferentes, fechas como string en 4 formatos, datos basura intercalados y filas que "parecen" vacías pero no lo son.

⚠️ Prerequisito: importar_temporeros e importar_cuarteles deben haberse ejecutado primero. Este comando busca temporeros y cuarteles en la BD — si no existen, rechaza las filas.

**Reutilizas el proyecto Django del Día 4.** Copia la carpeta a `25-04-2026/` y trabaja sobre esa copia.

### 📁 Estructura que debes crear

```
25-04-2026/
├── proyecto_django/
│   └── temporeros/
│       └── management/
│           └── commands/
│               ├── __init__.py
│               ├── importar_temporeros.py
│               ├── importar_labores.py
│               └── importar_cuarteles.py
├── datos/
│   ├── planilla_temporeros_marzo.xlsx
│   ├── registro_labores_semana_15.xlsx
│   └── cuarteles_actualizados.xlsx
├── logs/
├── utils/
│   └── rut.py
└── requirements.txt
```

---

## 📥 Los 3 archivos que te entrego

### Archivo 1 — `planilla_temporeros_marzo.xlsx` (~510 filas, 2 hojas)

| Hoja | Contenido |
|------|-----------|
| `Instrucciones` | Texto de RR.HH. con encabezados **falsos** — esta hoja no se importa |
| `Incorporación Marzo` | Los datos reales. Encabezados reales en fila 6, datos desde fila 7 |

**Problemas que contiene:**

| Problema | Cantidad aprox |
|----------|---------------|
| RUT con dígito verificador inválido | ~25 |
| RUT sin guión (`152345674`) | ~2 |
| RUT con puntos (`15.234.567-4`) | ~115 |
| RUT con letra incrustada en el número (`1234A567-8`) | ~1 |
| RUT con espacios (`  15234567 - 4  `) | ~1 |
| RUT que ya existe en tu BD | 3 |
| Nombres en MAYÚSCULAS | ~10 |
| Nombres con espacios al inicio/fin | ~20 |
| Fecha en formato `dd-mm-yyyy` | mezclado |
| Fecha en formato `yyyy-mm-dd` | mezclado |
| Fecha en formato americano `mm/dd/yyyy` (ambigua) | ~3 |
| Fecha como texto `"15 de marzo de 2026"` | ~3 |
| Fecha con siglo equivocado (`1926` en vez de `2026`) | ~2 |
| Fecha como objeto `datetime` real de Excel | ~30% |
| Supervisor con valores `"✓"`, `"x"`, `"YES"`, `1`, `True` | mezclado |
| Supervisor con valores inválidos `"quizás"`, `"?"`, `""` | ~10 |
| Talla en minúscula (`"s"`, `"xl"`) | ~6 |
| Talla inválida (`"XS"`, `"XXL"`, `"42"`) | ~12 |
| Campo activo con valores `"1"`, `"0"`, `True`, `False` | ~5% |
| Filas vacías | ~10 |
| Filas con solo espacios (no son `None`) | ~8 |
| Fila final con texto `"TOTAL INCORPORACIONES: ..."` | 1 |

### Archivo 2 — `registro_labores_semana_15.xlsx` (~1.875 filas, 7 hojas)

Una hoja por día de la semana. **Cada hoja tiene el encabezado real en una fila distinta y las columnas en un orden diferente.** No puedes asumir que la columna A siempre es el nombre del trabajador.

| Hoja | Fecha | Filas aprox | Tiene col. Fecha | Orden columnas |
|------|-------|------------|-----------------|----------------|
| `Lunes 30-03` | 30/03/2026 | ~330 | ❌ No | Trabajador, RUT, Cuartel, Tipo, Horas, Kilos, Obs |
| `Martes 31-03` | 31/03/2026 | ~320 | ❌ No | RUT, Nombre, Tipo, Cuartel, Kilos, Horas, Obs |
| `Miercoles 01-04` | 01/04/2026 | ~310 | ✅ Sí | Trabajador, N° RUT, Labor, Sector, Hrs, Kg cosechados, Fecha, Notas |
| `Jueves 02-04` | 02/04/2026 | ~295 | ✅ Sí | Nombre, RUT, Cuartel/Sector, Tipo de tarea, Fecha, Horas, Kg, Obs |
| `Viernes 03-04` | 03/04/2026 | ~285 | ✅ Sí | RUT, Trabajador, Cuartel, Tarea, Fecha, Horas trab., Kilos |
| `Sabado 04-04` | 04/04/2026 | ~185 | ✅ Sí | Nombre, RUT, Cuartel, Tipo, Horas, Kg, Fecha |
| `Domingo 05-04` | 05/04/2026 | ~95 | ❌ No | RUT, Trabajador, Tipo, Cuartel, Horas, Kilos |

**Problemas que contiene en todas las hojas:**

| Problema | Descripción |
|----------|-------------|
| Cuartel como `"A1"` en vez de `"A-1"` | Falta el guión |
| Cuartel como `"Cuartel A-1"` | Tiene prefijo |
| Cuartel como `"SECTOR A2"` | Mayúsculas + sin guión |
| Cuartel inexistente `"Z-99"` | No está en BD |
| Tipo en minúscula (`"cosecha"`, `"poda"`) | |
| Tipo con espacios (`"  Cosecha  "`) | |
| Tipo en inglés (`"Harvesting"`) | |
| Horas como `"7,5"` (coma decimal) | |
| Horas como `"8 hrs"` (con texto) | |
| Horas como `"aprox 8 horas"` | |
| Horas = 0 | |
| Horas negativas (`-3`) | |
| Horas > 12 (`15`, `24`) | |
| Kilos como `"120,5"` (coma decimal) | |
| Kilos como `"120 kg"` (con texto) | |
| Kilos negativos | |
| Kilos = `"ND"` | |
| Cosecha sin kilos | Debe rechazarse |
| No-cosecha con kilos | Debe forzar a `None` |
| RUT inexistente en BD | ~4% de filas |
| RUT con DV inválido | ~2% de filas |
| Duplicado dentro de la misma hoja | ~8 por hoja |
| Filas vacías intercaladas | ~3-7 por hoja |
| Fecha futura (año 2030) | ~1-2 por hoja |
| Fecha con siglo equivocado | ~1-2 por hoja |
| Fecha vacía (hojas que sí tienen col. Fecha) | ~15% de filas |

### Archivo 3 — `cuarteles_actualizados.xlsx` (~55 filas, 2 hojas)

| Hoja | Contenido |
|------|-----------|
| `Referencia` | Lista de variedades aprobadas — referencia, no se importa |
| `Maestro Cuarteles` | Datos reales. Encabezados en fila 4, datos desde fila 5 |

**Tiene 6 columnas:** Código Cuartel, Hectáreas, Variedad, Estado (Activo), Rendimiento esperado, Observaciones.

La columna `Rendimiento esperado` no existe en tu modelo — se ignora.

| Tipo de fila | Cantidad |
|-------------|---------|
| Cuarteles existentes en BD (actualizar) | 6 |
| Cuarteles nuevos válidos | ~40 |
| Duplicado dentro del mismo archivo | 1 |
| Inválidos (rechazar) | 6 |

**Typos en variedad que debes corregir automáticamente:**

| En el archivo | Corrección |
|--------------|-----------|
| `"Legasy"`, `"Legaci"` | `"Legacy"` |
| `"Bigitta"`, `"Brigita"`, `"Bridgitta"` | `"Brigitta"` |
| `"DUKE"`, `"duke"` | `"Duke"` |
| `"LEGACY"`, `"legacy"` | `"Legacy"` |
| `"BRIGITTA"`, `"brigitta"` | `"Brigitta"` |
| `"STAR"`, `"star"` | `"Star"` |

**Inválidos que deben rechazarse:**

| Código | Problema |
|--------|---------|
| X-1 | Hectáreas negativas (`-5,0`) |
| X-2 | Hectáreas como texto (`"cinco punto cinco"`) |
| X-3, X-4 | Variedad inexistente (`"Variedad X"`, `"Blueberry"`, etc.) |
| X-5 | Hectáreas = 0 |
| (vacío) | Código vacío |

---

## 🆔 Tarea 1: Módulo de validación de RUT

📄 **Archivo:** `25-04-2026/utils/rut.py`

### ✅ Lo que debes hacer

#### Función `calcular_dv(numero: int) -> str`

Recibe la parte numérica del RUT y devuelve el dígito verificador correcto.

**Algoritmo (módulo 11):**
1. Recorre los dígitos del número de derecha a izquierda.
2. Multiplica cada dígito por la secuencia `2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7, ...`
3. Suma todos los productos.
4. `resto = 11 - (suma % 11)`
5. Si `resto == 11` → retorna `"0"`. Si `resto == 10` → retorna `"K"`. Sino → retorna `str(resto)`.

#### Función `limpiar_rut(rut: str) -> str`

Recibe un RUT en cualquier formato posible y retorna `"XXXXXXXX-D"` normalizado (sin puntos, con guión, DV en mayúscula).

Debe manejar:
- `"15.234.567-4"` → `"15234567-4"`
- `"15234567-4"` → `"15234567-4"`
- `"152345674"` (sin guión, DV al final) → `"15234567-4"`
- `"15234567K"` → `"15234567-K"`
- `"  15234567 - 4  "` (con espacios) → `"15234567-4"`

Si el formato tiene caracteres inválidos en la parte numérica (letras que no sean el DV), lanza `ValueError`.

#### Función `validar_rut(rut: str) -> bool`

Limpia el RUT, calcula el DV correcto, compara. Retorna `True` si coincide, `False` si no.

#### Pruebas en `if __name__ == "__main__"`

| Entrada | Resultado esperado |
|---------|--------------------|
| `validar_rut("15234567-4")` | `True` |
| `validar_rut("15.234.567-4")` | `True` |
| `validar_rut("20123456-9")` | `False` (DV correcto es `5`) |
| `limpiar_rut("15.234.567-4")` | `"15234567-4"` |
| `limpiar_rut("15234567K")` | `"15234567-K"` |
| `limpiar_rut("  15234567 - 4  ")` | `"15234567-4"` |

---

## 📋 Tarea 2: Importador de temporeros

📄 **Archivo:** `management/commands/importar_temporeros.py`

```bash
python manage.py importar_temporeros datos/planilla_temporeros_marzo.xlsx
python manage.py importar_temporeros datos/planilla_temporeros_marzo.xlsx --dry-run
python manage.py importar_temporeros datos/planilla_temporeros_marzo.xlsx --update
```

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `archivo` | Ruta al `.xlsx` |
| `--dry-run` | No escribe en BD. Reporta qué haría. |
| `--update` | RUTs que ya existen en BD → actualiza. Sin este flag → salta. |

### Flujo

#### 1. Detectar la hoja correcta

El archivo tiene 2 hojas. **No uses `wb.active` ni el nombre hardcodeado.** Itera `wb.sheetnames`, lee las primeras filas de cada hoja y elige la que contenga una fila con `"RUT"` y alguna variante de `"Nombre"`. La hoja `Instrucciones` tiene texto pero no esos dos encabezados juntos.

#### 2. Detectar la fila de encabezados

Dentro de la hoja correcta, itera fila por fila hasta encontrar la primera que contenga `"RUT"`. Esa es la fila de headers.

#### 3. Mapear encabezados

```python
headers = {}
for cell in ws[header_row]:
    if cell.value:
        headers[str(cell.value).strip()] = cell.column - 1
```

Así no dependes del orden de columnas.

#### 4. Detectar y saltar filas basura

- Todos los valores `None` → ignorar.
- La celda del nombre tiene solo espacios → ignorar.
- La celda del nombre empieza con `"TOTAL"`, `"Versión"` o `"Aprobado"` → ignorar.

#### 5. Normalizar campo por campo

| Campo | Normalización |
|-------|--------------|
| **Nombre** | `strip()`. Si vacío → rechazar. Si en MAYÚSCULAS → `.title()`. |
| **RUT** | `limpiar_rut()` → si `ValueError` → rechazar + log. `validar_rut()` → si `False` → rechazar + log. |
| **Teléfono** | Quitar `+`, espacios, paréntesis. Si queda vacío → `None`. |
| **Contacto emergencia** | `strip()`. Si vacío → `None`. |
| **Fecha ingreso / nacimiento** | Si es `datetime` → `.date()`. Si es `str` → parsear con `%d/%m/%Y`, `%d-%m-%Y`, `%Y-%m-%d`, `%d.%m.%Y`. Si ninguno funciona → rechazar + log. |
| **Supervisor** | Verdadero: `{"Sí","SI","si","sí","S","s","x","✓","YES","yes","1",1,True}`. Falso: `{"No","NO","no","N","n","0",0,False,"false","FALSE"}`. Cualquier otro → rechazar + log. |
| **Talla** | `strip().upper()`. Validar que esté en `{"S","M","L","XL"}`. Si no → rechazar + log. |
| **Activo** | Mismo mapeo que Supervisor. Default `True` si vacío. |

#### 6. Inserción / actualización

- RUT ya existe + sin `--update` → saltar + log.
- RUT ya existe + `--update` → actualizar campos cambiados + log.
- No existe → crear.
- `--dry-run` → todo dentro de transacción con `rollback` al final.

### Output del comando

```
================================================================
IMPORTACIÓN DE TEMPOREROS — planilla_temporeros_marzo.xlsx
================================================================
Hoja utilizada:               Incorporación Marzo
Filas totales leídas:                511
Filas vacías/basura ignoradas:        21
Filas procesadas:                    490
  ├─ Creados:                        410
  ├─ Actualizados:                     0  (--update no activo)
  └─ Saltados (ya existen):            3
Filas rechazadas:                     52
  ├─ RUT inválido (DV):               25
  ├─ RUT formato inválido:             2
  ├─ Talla inválida:                  12
  ├─ Supervisor inválido:             10
  └─ Fecha inválida:                   3
         (una fila puede tener más de un error — se cuenta el primero)
Modo:                         DRY-RUN (no se escribió nada)
================================================================
Log: logs/import_temporeros_2026-04-25_14-32-15.log
```

### Formato del log

```
[FILA 007] OK creado       : Roberto Salinas (15234567-4)
[FILA 012] RECHAZADO RUT   : DV inválido. Valor recibido: '20123456-9' → Andrés Soto
[FILA 015] RECHAZADO TALLA : 'XS' no válida. Válidas: S/M/L/XL → Romina Acuña
[FILA 018] IGNORADO        : fila vacía
[FILA 022] SALTADO         : RUT '11111111-1' ya existe en BD → Juan Pérez (copia)
[FILA 034] RECHAZADO FECHA : no se pudo parsear '15 de marzo de 2026' → Diego Ruiz
```

---

## 🌾 Tarea 3: Importador de labores

📄 **Archivo:** `management/commands/importar_labores.py`

```bash
python manage.py importar_labores datos/registro_labores_semana_15.xlsx
python manage.py importar_labores datos/registro_labores_semana_15.xlsx --dry-run
python manage.py importar_labores datos/registro_labores_semana_15.xlsx --hoja "Lunes 30-03"
```

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `archivo` | Ruta al `.xlsx` |
| `--dry-run` | No escribe en BD |
| `--hoja NOMBRE` | Procesa solo esa hoja. Sin este flag → todas. |

### Flujo por hoja

#### 1. Detectar la fila de encabezados

Cada hoja tiene el header en una fila diferente. Busca la primera fila que contenga alguno de: `"RUT"`, `"Trabajador"`, `"Nombre"`, `"Nombre Completo"`, `"Nombre del trabajador"`.

#### 2. Detectar si la hoja tiene columna de fecha

Verifica si el mapeo de encabezados contiene alguna variante de `"Fecha"`. Si no → la fecha viene del nombre de la hoja.

#### 3. Extraer fecha del nombre de hoja

Si la hoja no tiene columna de fecha (o la celda está vacía), parsea la fecha del título. Formato: `"DíaNombre DD-MM"`. Ejemplos:
- `"Lunes 30-03"` → `date(2026, 3, 30)`
- `"Domingo 05-04"` → `date(2026, 4, 5)`

Asume que el año es siempre 2026.

#### 4. Mapear encabezados — igual que antes

Los nombres de columna varían por hoja. Construye el diccionario `{nombre_col: indice}`. Para buscar el dato correcto, mapea variantes:

| Dato | Posibles nombres en el archivo |
|------|-------------------------------|
| `rut` | `"RUT"`, `"N° RUT"`, `"RUT Trabajador"` |
| `nombre` | `"Trabajador"`, `"Nombre"`, `"Nombre Completo"`, `"Nombre del trabajador"` |
| `cuartel` | `"Cuartel"`, `"Sector"`, `"Cuartel/Sector"` |
| `tipo` | `"Tipo Labor"`, `"Tipo de Labor"`, `"Tipo"`, `"Tipo de tarea"`, `"Labor"`, `"Tarea"` |
| `horas` | `"Horas"`, `"Hrs"`, `"Horas trabajadas"`, `"Horas trab."` |
| `kilos` | `"Kilos"`, `"Kg"`, `"Kg cosechados"`, `"Kilos cosechados"`, `"Kilos (solo cosecha)"` |
| `fecha` | `"Fecha"`, `"Fecha de trabajo"` |
| `obs` | `"Observaciones"`, `"Obs"`, `"Notas"` |

#### 5. Normalizar por campo

| Campo | Normalización |
|-------|--------------|
| **RUT** | `limpiar_rut()` + `validar_rut()`. Si inválido → rechazar. Buscar `Temporero` por RUT. Si no existe → rechazar. |
| **Cuartel** | Quitar prefijos `"Cuartel "`, `"CUARTEL "`, `"Sector "`, `"SECTOR "`. Quitar espacios. Si patrón `LetraNúmero` sin guión (`"A1"`) → insertar guión (`"A-1"`). `upper()`. Buscar `Cuartel` por nombre. Si no existe → rechazar. |
| **Tipo** | `strip().capitalize()`. Si no está en `{"Poda","Cosecha","Riego","Pesticida","Limpieza"}` → rechazar. |
| **Fecha** | Si tiene columna y valor → parsear mismos formatos. Si vacía → usar fecha de la hoja. Si futura → rechazar. Si anterior a `fecha_ingreso` del temporero → rechazar. |
| **Horas** | Convertir a `Decimal`. Aceptar: número, `"7.5"`, `"7,5"`, `"8 hrs"`, `"aprox 8 horas"` (extraer el número con regex). Si ≤ 0 o > 12 → rechazar. |
| **Kilos** | Convertir a `Decimal`. Aceptar: número, `"120 kg"`, `"120,5"`. Si `tipo == "Cosecha"` y kilos vacío o no convertible → rechazar. Si `tipo != "Cosecha"` y hay kilos → forzar `None`. |
| **Observaciones** | `strip()`. Si vacío → `""`. |

#### 6. Inserción

`labor.full_clean(); labor.save()`. Capturar `IntegrityError` por `UniqueConstraint` → loggear como duplicado (no como error de validación).

### Output del comando

```
================================================================
IMPORTACIÓN DE LABORES — registro_labores_semana_15.xlsx
================================================================

Hoja: Lunes 30-03     (30/03/2026, sin col. Fecha)
  Leídas: 339  |  Importadas: 298  |  Rechazadas: 26  |  Duplicadas: 8  |  Vacías: 7

Hoja: Martes 31-03    (31/03/2026, sin col. Fecha)
  Leídas: 325  |  Importadas: ...

Hoja: Miercoles 01-04 (01/04/2026, con col. Fecha)
  Leídas: 314  |  Importadas: ...

Hoja: Jueves 02-04    ...
Hoja: Viernes 03-04   ...
Hoja: Sabado 04-04    ...
Hoja: Domingo 05-04   ...

================================================================
TOTALES
  Filas leídas:              1.879
  Importadas:                1.634
  Rechazadas:                  197
    ├─ Horas fuera de rango:    38
    ├─ Cuartel no existe:       12
    ├─ Temporero no existe:     18
    ├─ Fecha inválida:          15
    ├─ Tipo inválido:           10
    └─ Cosecha sin kilos:        9
  Duplicadas (UniqueConstraint): 48
================================================================
Log: logs/import_labores_2026-04-25_15-10-44.log
```

---

## 🗺️ Tarea 4: Importador de cuarteles

📄 **Archivo:** `management/commands/importar_cuarteles.py`

```bash
python manage.py importar_cuarteles datos/cuarteles_actualizados.xlsx
python manage.py importar_cuarteles datos/cuarteles_actualizados.xlsx --dry-run
```

### Flujo

#### 1. Detectar la hoja correcta

El archivo tiene 2 hojas. Elige la que contenga una fila con `"Código"` o `"Código Cuartel"`. No uses el nombre hardcodeado.

#### 2. Detectar fila de encabezados — igual que antes.

#### 3. Ignorar columnas desconocidas

La columna `"Rendimiento esperado (kg/ha)"` no existe en el modelo. Si al mapear aparece una key desconocida → ignorar silenciosamente.

#### 4. Normalizar

| Campo | Normalización |
|-------|--------------|
| **Código** | `strip()`. Si vacío o solo espacios → ignorar fila. |
| **Hectáreas** | `str(v).replace(",", ".")`. `Decimal(...)`. Si falla o resultado ≤ 0 → rechazar. |
| **Variedad** | `strip()`. Aplicar diccionario de correcciones. `.title()`. Si no está en `{"Duke","Legacy","Brigitta","Star"}` → rechazar. |
| **Activo** | Mismo mapeo que supervisor en temporeros. |

#### 5. Lógica de upsert

- Si existe con el mismo `nombre`: comparar campos. Si cambian → `update_fields=[...]` con solo los distintos, loggear diferencia. Si no cambia nada → loggear como sin cambios.
- Si el código aparece más de una vez en el archivo → primera instancia procesa, segunda instancia → loggear como duplicado en archivo.
- Si no existe → crear.

### Output

```
================================================================
IMPORTACIÓN DE CUARTELES — cuarteles_actualizados.xlsx
================================================================
Hoja utilizada:     Maestro Cuarteles
Filas leídas:                  59
Filas vacías/basura ignoradas:  5
Procesadas:                    54
  ├─ Creados:                  40
  ├─ Actualizados:              4  (B-1: hectareas; B-2: variedad+activo; ...)
  ├─ Sin cambios:               2  (A-1, C-1)
  └─ Duplicado en archivo:      1  (A-1 — segunda aparición ignorada)
Rechazados:                     7
  ├─ Hectáreas inválidas:       3  (X-1, X-2, X-5)
  ├─ Código vacío:              1
  └─ Variedad inválida:         2  (X-3, X-4)
================================================================
Log: logs/import_cuarteles_2026-04-25_16-00-12.log
```

---

## 🚨 Reglas obligatorias del día

1. **Prohibido pandas.** Solo `openpyxl`. Itera celdas.
2. **Sin `except Exception` desnudos.** Cada validación captura su excepción específica.
3. **Idempotente.** Correr cualquier comando 2 veces no duplica datos.
4. **Cada ejecución genera un log** en `logs/import_<comando>_<fecha-hora>.log`.
5. **`--dry-run` usa rollback de transacción**, no un flag que omite el `.save()`.

---

## ✅ Verificaciones antes del commit

- [ ] `python utils/rut.py` corre y todas las pruebas pasan.
- [ ] `python manage.py importar_temporeros datos/planilla_temporeros_marzo.xlsx --dry-run` reporta sin escribir nada.
- [ ] Mismo sin `--dry-run` crea ~410 temporeros. Re-corrida sin `--update` → 0 creados, ~410 saltados.
- [ ] `python manage.py importar_cuarteles datos/cuarteles_actualizados.xlsx` actualiza los 6 existentes + crea ~40 nuevos + rechaza los inválidos.
- [ ] `python manage.py importar_labores datos/registro_labores_semana_15.xlsx` procesa las 7 hojas y el total importado supera 1.500.
- [ ] `python manage.py importar_labores ... --hoja "Lunes 30-03"` procesa solo esa hoja.
- [ ] Los logs se generan con una línea por fila procesada.
- [ ] `requirements.txt` incluye `openpyxl`.

---

## 📤 Entrega

```
25-04-2026/
├── proyecto_django/
│   └── temporeros/
│       └── management/
│           └── commands/
│               ├── __init__.py
│               ├── importar_temporeros.py
│               ├── importar_labores.py
│               └── importar_cuarteles.py
├── datos/
│   ├── planilla_temporeros_marzo.xlsx
│   ├── registro_labores_semana_15.xlsx
│   └── cuarteles_actualizados.xlsx
├── logs/
├── utils/
│   └── rut.py
└── requirements.txt
```

`git add`, `git commit -m "dia 05 - importadores excel"`, `git push`.