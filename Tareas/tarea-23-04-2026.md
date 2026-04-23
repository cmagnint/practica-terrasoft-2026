# 📘 Día 3 — Django: el ORM te reemplaza el SQL

---

## 🛠️ Antes de empezar: qué vamos a hacer

Hoy vas a levantar un proyecto Django completo que se conecta a PostgreSQL, definir un modelo, generar migraciones y escribir scripts que consulten la base usando el ORM.

### 📁 Estructura que debes crear

Dentro del repositorio, crea una carpeta llamada `23-04-2026`. **Todo el trabajo del día va dentro de esta carpeta.**

### 📋 Qué vas a entregar

Al final del día, la carpeta `23-04-2026/` debe contener:

| Archivo / Carpeta | Contenido | ¿Es obligatorio? |
|-------------------|-----------|------------------|
| `proyecto_django/` | Proyecto Django completo: carpeta del proyecto (`campo/`), carpeta de la app (`temporeros/`), archivo `manage.py`, y la carpeta `migrations/` con tus migraciones generadas | ✅ Sí |
| `requirements.txt` | Todas las dependencias del proyecto generadas con `pip freeze` | ✅ Sí |
| `consultas_orm.py` | Script con las 8 consultas del ORM (Tarea 3) | ✅ Sí |
| `reportes.py` | Script ejecutable que imprime el reporte (Tarea 4) | ✅ Sí |
| `.gitignore` | Archivo en la raíz del repo que excluya venv, `__pycache__`, archivos del IDE | ✅ Sí |

**NO debes subir:**
- Carpeta del virtualenv
- Archivos `__pycache__/`
- Archivos `*.pyc`
- Archivos del editor (`.vscode/`, `.idea/`)
- Archivos de sistema (`.DS_Store`, etc.)

---

## 🏗️ Tarea 1: Levantar el proyecto Django

📄 **Ubicación:** `23-04-2026/`

### ✅ Lo que debes hacer

#### 1️⃣ Entorno virtual y dependencias

- [ ] Crea un nuevo virtualenv dentro de `23-04-2026/`
- [ ] Activa el entorno
- [ ] Instala **Django** (última versión estable)
- [ ] Instala **`psycopg2-binary`** (driver PostgreSQL para Python)
- [ ] Genera el `requirements.txt` con `pip freeze`

#### 2️⃣ Base de datos nueva

- [ ] Desde `psql` como usuario `postgres`, crea una base de datos llamada `temporada_django`, propiedad del usuario `admin`.

#### 3️⃣ Crear el proyecto y la app

- [ ] Crea un proyecto Django llamado `campo`
- [ ] Dentro del proyecto, crea una app llamada `temporeros`

#### 4️⃣ Configurar la conexión a PostgreSQL

- [ ] Abre `settings.py` y busca la variable `DATABASES`
- [ ] Cámbiala de SQLite (el default) a PostgreSQL, apuntando a la base `temporada_django`
- [ ] Los parámetros de conexión son:
  - ENGINE: `django.db.backends.postgresql`
  - NAME: `temporada_django`
  - USER: `admin`
  - PASSWORD: `admin123`
  - HOST: `localhost`
  - PORT: `5432`
- [ ] Registra tu app `temporeros` en `INSTALLED_APPS`

#### 5️⃣ Primera migración

- [ ] Aplica las migraciones iniciales de Django.
- [ ] Conéctate con `psql` a la base `temporada_django` y lista las tablas con `\dt`. Guarda el output en un comentario al inicio de `consultas_orm.py`.

---

## 🧩 Tarea 2: El modelo Temporero

📄 **Ubicación:** `23-04-2026/proyecto_django/temporeros/models.py`

### ✅ Lo que debes hacer

#### 1️⃣ Define el modelo

En `models.py`, crea una clase `Temporero` con los siguientes campos:

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `nombre` | CharField | max_length=100, obligatorio |
| `rut` | CharField | max_length=12, único, obligatorio |
| `telefono` | CharField | max_length=20, opcional (null=True, blank=True) |
| `contacto_emergencia` | CharField | max_length=100, opcional |
| `fecha_ingreso` | DateField | obligatorio |
| `supervisor` | BooleanField | default=False |
| `fecha_nacimiento` | DateField | obligatorio |
| `talla_polera` | CharField | max_length=2, con `choices` restringido a 'S', 'M', 'L', 'XL' |
| `activo` | BooleanField | default=True |

#### 2️⃣ Genera la migración

- [ ] Genera el archivo de migración correspondiente a tu nuevo modelo.
- [ ] Abre el archivo generado (algo tipo `0001_initial.py`). **Léelo completo.**

#### 3️⃣ Ver el SQL que Django escribiría

- [ ] Ejecuta el subcomando de `manage.py` que muestra el SQL de una migración específica, sin ejecutarla.


#### 4️⃣ Aplica la migración

- [ ] Aplica la migración a la base de datos.
- [ ] Conéctate con `psql` a `temporada_django` y verifica con `\dt` que apareció una tabla nueva llamada `temporeros_temporero`.
- [ ] Ejecuta `\d temporeros_temporero` en psql para ver la estructura. Guarda el output como comentario en `consultas_orm.py`.

---

## 💻 Tarea 3: Usar el ORM en lugar de SQL

📄 **Archivo:** `23-04-2026/consultas_orm.py`

### ✅ Lo que debes hacer

#### 1️⃣ Entra al shell de Django

Usa el subcomando de `manage.py` que abre una consola Python con Django precargado.

#### 2️⃣ Crea datos de prueba

Crea **15 temporeros** desde el shell, con los siguientes casos obligatorios:

- 5 supervisores y 10 no-supervisores
- 2 temporeros con `activo=False`
- 3 temporeros sin teléfono (valor `None`)
- 1 temporero mayor de 60 años
- 1 temporero menor de 22 años
- 2 temporeros con la misma `fecha_ingreso`
- Al menos 1 temporero con cada talla de polera (S, M, L, XL)

Puedes usar `Temporero.objects.create(...)` o instanciar y llamar `.save()`.

#### 3️⃣ Resuelve las 8 consultas


**Nivel básico:**

1. Listar todos los temporeros activos ordenados por fecha de ingreso (más nuevo primero).
2. Buscar un temporero por su RUT. Si no existe, atrapa la excepción `Temporero.DoesNotExist` e imprime un mensaje claro.
3. Contar cuántos supervisores activos hay.
4. Marcar un temporero como inactivo usando `.filter().update()`. **Prohibido usar `.delete()`.**

**Nivel intermedio:**

5. Obtener los nombres de los temporeros cuyo nombre empieza con 'J' o 'M', case-insensitive. Usa el lookup `__iregex` o combina `__istartswith` con un `Q()` de OR.
6. Obtener cuántos temporeros hay por cada talla de polera, ordenados de mayor a menor. Usa `values('talla_polera').annotate(total=Count('id')).order_by('-total')`.
7. Calcular el promedio de edad de los supervisores, y en una consulta separada el promedio de edad de los no-supervisores. Usa `aggregate()` con `Avg()` y una expresión que calcule la edad desde `fecha_nacimiento`. Necesitas importar `ExpressionWrapper`, `F`, y funciones de fecha.

**Nivel avanzado:**

8. Agrupa los temporeros activos en tres rangos de edad y cuenta cuántos hay en cada uno:
   - Menores de 30
   - Entre 30 y 50 (inclusive)
   - Mayores de 50
   
   Usa `Case`, `When` y `Value` de `django.db.models` combinados con `annotate()` y `values()`. **Debe resolverse con una sola consulta al ORM, no con loops de Python.**

---

## 🛠️ Tarea 4: Script de reportes automáticos

📄 **Archivo:** `23-04-2026/reportes.py`

El jefe de campo te dice:

> 📝 *"Oye, necesito que me armes un programita que pueda correr cuando yo quiera y me imprima un resumen con todo lo importante: cuántos temporeros hay, cuántos supervisores, cuántos por cada talla, cuál es el más antiguo, el más joven, etc. La idea es que lo pueda correr todos los lunes para tener el estado actualizado del equipo. Y que se vea bonito en la consola, no un pegote de datos."*

### ✅ Lo que debes hacer

Crea un archivo `reportes.py` en `23-04-2026/` que se ejecute con `python reportes.py` desde la terminal. **Todas las consultas deben usar el ORM de Django, ninguna debe usar SQL crudo.**

#### 1️⃣ Configuración standalone de Django

Un script Python fuera del shell no sabe nada de Django. Al inicio del archivo, incluye este bloque **exactamente** (adapta solo el nombre del módulo de settings):

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero
```

#### 2️⃣ Estructura del reporte

El reporte debe imprimir **5 secciones obligatorias**, en este orden:

**Sección 1 — Resumen general**

```
--- RESUMEN GENERAL ---
Total registrados:        [N]
Activos:                  [N]
Inactivos:                [N]
Supervisores activos:     [N]
```

**Sección 2 — Distribución por talla de polera** (solo activos)

Tabla con 3 columnas: TALLA, CANTIDAD, PORCENTAJE. Ordenada de mayor a menor cantidad. Porcentaje con 1 decimal.

```
--- DISTRIBUCIÓN POR TALLA ---
TALLA    CANTIDAD    PORCENTAJE
  M         8          53.3%
  L         4          26.7%
  S         2          13.3%
  XL        1           6.7%
```

**Sección 3 — Rangos de edad** (solo activos)

4 rangos:
- Menores de 25 años
- Entre 25 y 40 años (inclusive)
- Entre 41 y 55 años (inclusive)
- Mayores de 55 años

Cada rango debe mostrar la cantidad y el porcentaje del total de activos.

**Sección 4 — Datos destacados**

- El temporero **más antiguo en la empresa** (mayor antigüedad desde `fecha_ingreso`): nombre + fecha de ingreso
- El temporero **más joven** (por `fecha_nacimiento`): nombre + edad calculada
- El temporero **más viejo** (por `fecha_nacimiento`): nombre + edad calculada
- **Promedio de edad** del equipo activo (con 1 decimal)

**Sección 5 — Alertas**

Muestra solo las alertas que correspondan. Si no hay ninguna, imprime `✅ Sin alertas.`

Cada alerta debe mostrar cuántos casos hay Y listar los nombres:

```
⚠️  Temporeros activos sin teléfono: 3
   - Juan Pérez
   - María González
   - Pedro Soto

⚠️  Temporeros activos sin contacto de emergencia: 1
   - Ana Díaz

⚠️  Supervisores activos menores de 25 años: 1
   - Diego Muñoz (22 años)
```

#### 3️⃣ Formato de salida obligatorio

- Cada sección separada por una línea de `=` de 64 caracteres de ancho
- Títulos de sección en mayúscula entre `--- TÍTULO ---`
- Primera línea del reporte: `REPORTE DE TEMPOREROS - Generado el DD/MM/YYYY a las HH:MM`
- Usa `datetime.now()` para la fecha/hora
- Las tablas deben tener columnas alineadas usando `f-strings` con padding, por ejemplo: `f"{talla:<8} {cantidad:>5} {porcentaje:>10.1f}%"`

**Ejemplo de cómo debe verse el inicio:**

```
================================================================
REPORTE DE TEMPOREROS - Generado el 23/04/2026 a las 14:30
================================================================

--- RESUMEN GENERAL ---
Total registrados:        17
Activos:                  15
Inactivos:                 2
Supervisores activos:      5

================================================================

--- DISTRIBUCIÓN POR TALLA ---
TALLA    CANTIDAD    PORCENTAJE
  M         8          53.3%
  L         4          26.7%
  S         2          13.3%
  XL        1           6.7%

================================================================
```

#### 4️⃣ Argumento de línea de comandos

Usa el módulo `argparse` de la librería estándar de Python para aceptar el argumento `--solo-activos`.

- Sin argumento (`python reportes.py`): imprime las 5 secciones completas.
- Con el argumento (`python reportes.py --solo-activos`): omite la Sección 1 (Resumen general) y la sección de datos destacados excluye temporeros inactivos.

#### 5️⃣ Verificaciones antes de entregar

- [ ] `python reportes.py` corre sin errores
- [ ] `python reportes.py --solo-activos` corre sin errores y se ve diferente al anterior
- [ ] Los porcentajes de la sección 2 suman 100% (± 0.1% por redondeo)
- [ ] No hay un solo `cursor.execute()` ni SQL crudo en el archivo
- [ ] Las alertas efectivamente detectan los casos (pruébalo creando un temporero sin teléfono y volviendo a correr el script)
- [ ] El formato es legible: columnas alineadas, separadores visibles, nada aplastado

---

## 📤 Entrega

Tu carpeta `23-04-2026/` debe contener:

```
23-04-2026/
├── proyecto_django/
│   ├── campo/
│   ├── temporeros/
│   │   ├── migrations/
│   │   ├── models.py
│   │   └── ...
│   └── manage.py
├── requirements.txt
├── consultas_orm.py
└── reportes.py
```

Y en la raíz del repositorio debe existir un archivo `.gitignore` correctamente configurado.

### Verificaciones finales antes del commit

- [ ] `git status` **no muestra** la carpeta del venv
- [ ] `git status` **no muestra** archivos `__pycache__/`
- [ ] `git status` **no muestra** archivos `.pyc`
- [ ] El `requirements.txt` incluye Django y psycopg2-binary con versiones
- [ ] Los 4 archivos principales (`consultas_orm.py`, `reportes.py`, `models.py`, `settings.py`) están guardados y funcionan

Súbelo al repositorio con el flujo de git que ya conoces: `git add`, `git commit`, `git push`.