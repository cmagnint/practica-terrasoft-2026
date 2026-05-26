# 📘 Día 4 — Relaciones entre modelos: Labores y Temporeros

---

## 🛠️ Antes de empezar: qué vamos a hacer

**Reutilizas el proyecto Django del Día 3.** Copia la carpeta a `24-04-2026/` y extiéndela con dos modelos nuevos.

### 📁 Estructura que debes crear

```
24-04-2026/
├── proyecto_django/    ← copia del Día 3 + los nuevos modelos
├── requirements.txt
├── poblar_datos.py     ← script que genera datos masivos de prueba
├── consultas_orm.py    ← 10 consultas con relaciones
├── reportes.py         ← reporte extendido con información de labores
└── .gitignore
```

### 📋 Qué vas a entregar

| Archivo / Carpeta | Contenido | ¿Es obligatorio? |
|-------------------|-----------|------------------|
| `proyecto_django/` | Proyecto Django con los 3 modelos (`Temporero`, `Cuartel`, `Labor`) y sus migraciones | ✅ Sí |
| `requirements.txt` | Dependencias del proyecto | ✅ Sí |
| `poblar_datos.py` | Script standalone que puebla la base con datos masivos | ✅ Sí |
| `consultas_orm.py` | 10 consultas con relaciones resueltas con el ORM | ✅ Sí |
| `reportes.py` | Reporte extendido con datos de labores | ✅ Sí |

---

## 🏗️ Tarea 1: Dos modelos nuevos con relaciones

📄 **Archivo:** `24-04-2026/proyecto_django/temporeros/models.py`

El jefe de campo te dice:

> 📝 *"Ya tenemos el registro de temporeros funcionando, pero necesito empezar a llevar el control del trabajo del día a día. Cada temporero hace distintas labores: poda, cosecha, riego, aplicación de pesticidas, limpieza. Las labores se hacen en los cuarteles del fundo. Cada cuartel tiene un nombre (A, B, C, etc.), una superficie en hectáreas y una variedad de arándano distinta. Un mismo temporero puede hacer varias labores en el día, y a veces cambia de cuartel. Necesito saber cuántas horas trabajó cada uno, en qué cuartel y en qué labor."*

### ✅ Lo que debes hacer

#### 1️⃣ Modelo `Cuartel`

Agrega al archivo `models.py` una clase `Cuartel` con los siguientes campos:

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `nombre` | CharField | max_length=50, único, obligatorio |
| `hectareas` | DecimalField | max_digits=6, decimal_places=2, obligatorio |
| `variedad` | CharField | max_length=50, con `choices`: 'Duke', 'Legacy', 'Brigitta', 'Star' |
| `activo` | BooleanField | default=True |

Agrega un método `__str__` que devuelva: `f"Cuartel {self.nombre} - {self.variedad}"`

#### 2️⃣ Modelo `Labor`

Agrega una clase `Labor` con los siguientes campos:

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `temporero` | ForeignKey | a `Temporero`, on_delete=PROTECT, related_name='labores' |
| `cuartel` | ForeignKey | a `Cuartel`, on_delete=PROTECT, related_name='labores' |
| `tipo` | CharField | max_length=30, con `choices`: 'Poda', 'Cosecha', 'Riego', 'Pesticida', 'Limpieza' |
| `fecha` | DateField | obligatorio |
| `horas_trabajadas` | DecimalField | max_digits=4, decimal_places=2, obligatorio |
| `kilos_cosechados` | DecimalField | max_digits=7, decimal_places=2, null=True, blank=True (solo aplica cuando `tipo='Cosecha'`) |
| `observaciones` | TextField | blank=True |

Agrega un método `__str__` que devuelva: `f"{self.temporero.nombre} - {self.tipo} en {self.cuartel.nombre} ({self.fecha})"`

#### 3️⃣ Validaciones a nivel de modelo

Sobreescribe el método `clean()` del modelo `Labor` para validar:

- Las `horas_trabajadas` deben estar entre 0 y 12 (inclusive). Si no, lanzar `ValidationError`.
- Si `tipo == 'Cosecha'`, el campo `kilos_cosechados` **es obligatorio**.
- Si `tipo != 'Cosecha'`, el campo `kilos_cosechados` **debe ser null**.
- La `fecha` de la labor no puede ser anterior a la `fecha_ingreso` del temporero.
- La `fecha` de la labor no puede ser futura.

> 💡 Importa `ValidationError` desde `django.core.exceptions`.

#### 4️⃣ Reglas de negocio adicionales

Agrega al modelo `Labor` una clase `Meta` con:
- `ordering = ['-fecha', 'temporero__nombre']`
- Una `UniqueConstraint` que impida que un mismo temporero haga el mismo tipo de labor en el mismo cuartel el mismo día. Investiga la sintaxis de `UniqueConstraint` con `fields` y `name`.

#### 5️⃣ Genera y aplica las migraciones

- [ ] Genera las migraciones correspondientes
- [ ] Aplícalas a la base de datos
- [ ] Verifica con `psql` que existen las tablas `temporeros_cuartel` y `temporeros_labor`
- [ ] Con `\d temporeros_labor` revisa que las FK aparezcan correctamente como `REFERENCES`

---

## 🌱 Tarea 2: Script para poblar datos masivos

📄 **Archivo:** `24-04-2026/poblar_datos.py`

Con 15 temporeros y 0 labores no puedes hacer consultas interesantes. Necesitas **datos realistas y variados**. Este script los genera.

### ✅ Lo que debes hacer

#### 1️⃣ Configuración standalone del script

Al inicio del archivo, configura Django igual que en `reportes.py` del Día 3.

#### 2️⃣ Limpiar datos anteriores

El script debe empezar **borrando** los datos existentes de `Labor` y `Cuartel` (NO los temporeros). Usa `.all().delete()`. Imprime un mensaje como `"✓ Datos anteriores limpiados"`.

#### 3️⃣ Crear cuarteles

Crea exactamente **6 cuarteles** con estas especificaciones:

| Nombre | Hectáreas | Variedad |
|--------|-----------|----------|
| A-1 | 5.50 | Duke |
| A-2 | 8.25 | Duke |
| B-1 | 12.00 | Legacy |
| B-2 | 6.75 | Brigitta |
| C-1 | 10.50 | Legacy |
| C-2 | 4.00 | Star |

Usa `bulk_create()` para crearlos de una sola vez. Investiga qué hace y en qué se diferencia de `create()` en bucle.

#### 4️⃣ Generar labores masivas

Genera **al menos 200 labores** con datos aleatorios pero coherentes. Usa el módulo `random` y `datetime`.

**Reglas obligatorias para la generación:**

- [ ] Las fechas deben estar **entre 30 y 1 días atrás** (desde hoy). Ninguna en el futuro.
- [ ] Cada temporero activo debe tener **entre 5 y 25 labores** distribuidas aleatoriamente.
- [ ] **60% de las labores** deben ser de tipo 'Cosecha'. El resto repartido entre los otros tipos.
- [ ] Si el tipo es 'Cosecha', generar `kilos_cosechados` aleatorio entre 20 y 150 (con 2 decimales).
- [ ] Si el tipo NO es 'Cosecha', `kilos_cosechados` debe ser `None`.
- [ ] Las `horas_trabajadas` deben estar entre 2 y 10 (con 1 o 2 decimales).
- [ ] El 20% de las labores debe tener `observaciones` (generar textos cortos como "Sector norte", "Lluvia leve", "Turno tarde"). El resto en blanco.

**Manejo de duplicados:**

Recuerda la `UniqueConstraint` del modelo: no puede existir dos veces la misma combinación `(temporero, cuartel, tipo, fecha)`. Tu script debe:

- [ ] Capturar la excepción `IntegrityError` de `django.db`
- [ ] Cuando ocurra, saltar ese registro e intentar con otro
- [ ] Contar cuántos duplicados se saltaron y reportarlo al final

#### 5️⃣ Reporte final del script

Al terminar, el script debe imprimir un resumen:

```
================================================================
DATOS POBLADOS CORRECTAMENTE
================================================================
Cuarteles creados:              6
Labores creadas:              N
Labores duplicadas saltadas:  N
Temporeros con labores:       N
Tiempo total de ejecución:    N.NN segundos
================================================================
```

Usa `time.time()` al inicio y al final para calcular el tiempo.

---

## 💻 Tarea 3: Consultas con relaciones

📄 **Archivo:** `24-04-2026/consultas_orm.py`

Esta tarea es el **corazón del día**. Aquí practicas las consultas que un backend real necesita todos los días.

### ✅ Lo que debes hacer

Resuelve las siguientes 10 consultas usando el ORM de Django. **Cada una debe estar en el archivo con su número, descripción y código.**

**Regla de oro:** Ninguna consulta debe hacer loops de Python para calcular cosas que la BD puede hacer. Todo lo agregable se agrega en la query.

#### Nivel 1 — Relaciones básicas (3 consultas)

**Consulta 1 — Forward relation:** Obtener todas las labores del temporero con RUT `'12345678-9'`.
> Pista: usas `Labor.objects.filter(temporero__rut=...)`. La doble underscore (`__`) es la sintaxis de Django para atravesar relaciones.

**Consulta 2 — Reverse relation:** Dado un temporero obtenido por `Temporero.objects.get(rut='12345678-9')`, accede a todas sus labores usando el `related_name` que definiste en la ForeignKey.

**Consulta 3 — Filtrado por campo de modelo relacionado:** Todas las labores realizadas en cuarteles de variedad `'Duke'`.

#### Nivel 2 — Agregaciones con relaciones (4 consultas)

**Consulta 4 — Total de horas por temporero:** Para cada temporero activo, obtener el total de horas trabajadas en todas sus labores. Ordenado de mayor a menor. Debe devolver una lista con `nombre`, `rut` y `total_horas`.

> Pista: `Temporero.objects.filter(activo=True).annotate(total_horas=Sum('labores__horas_trabajadas')).order_by('-total_horas')`

**Consulta 5 — Cuartel más productivo:** Cuál es el cuartel con más kilos cosechados en total. Devuelve el nombre del cuartel y el total. (Una sola fila como resultado, no un ranking).

**Consulta 6 — Ranking de tipos de labor:** Cuántas labores hay por cada tipo, ordenadas de mayor a menor. Incluye el porcentaje del total.

> Pista: puedes hacer dos queries (una para el total, otra con `.values('tipo').annotate(cantidad=Count('id'))`) y calcular el porcentaje al final, o investigar cómo hacerlo en una sola query con subqueries.

**Consulta 7 — Promedio de kilos por labor de cosecha, por cuartel:** Para cada cuartel, calcular el promedio de `kilos_cosechados` considerando solo las labores de tipo 'Cosecha'. Ordenado por promedio descendente.

#### Nivel 3 — Consultas complejas (3 consultas)

**Consulta 8 — Temporeros sin labores en la última semana:** Lista de temporeros activos que **no tienen ninguna labor registrada** en los últimos 7 días. Útil para el jefe porque indica ausencias.

> Pista: usa `exclude()` con un subquery, o mejor aún, investiga `annotate()` con un `Count()` filtrado (`Count('labores', filter=Q(labores__fecha__gte=...))`) y luego filtrar por `count=0`.

**Consulta 9 — Top 3 temporeros cosecheros del mes:** Los 3 temporeros que más kilos cosecharon en los últimos 30 días. Devuelve nombre, total de kilos y cantidad de labores de cosecha realizadas.

**Consulta 10 — Reporte cruzado:** Matriz de cuántas labores hay por cada combinación de **cuartel + tipo de labor**. El resultado debe poder imprimirse como una tabla donde las filas son cuarteles y las columnas son tipos.

> Este es el más difícil. Puedes hacerlo con un queryset que agrupe por ambos campos y luego reorganizar el resultado en Python (con un dict) para imprimirlo como matriz. Es válido usar Python para la reorganización final, pero la **agregación** debe ser del ORM.

### Formato obligatorio para cada consulta

```python
# ============================================================
# Consulta N: [descripción corta]
# ============================================================

# Código ORM:
resultado = ...

# Imprimir el resultado de forma legible:
for item in resultado:
    print(item)
```

---

## 📊 Tarea 4: Reporte extendido con labores

📄 **Archivo:** `24-04-2026/reportes.py`

Extiende el `reportes.py` del Día 3 para incluir **tres secciones nuevas** relacionadas con las labores. El script debe seguir funcionando con `python reportes.py` y con `python reportes.py --solo-activos` como antes.

### ✅ Lo que debes hacer

Agrega al reporte las siguientes secciones **después** de las 5 del Día 3:

#### Sección 6 — Resumen de labores

```
--- RESUMEN DE LABORES (últimos 30 días) ---
Total de labores:             200
Total de horas trabajadas:    N
Total de kilos cosechados:    N
Labores de cosecha:           N (N%)
Labores de otras tareas:      N (N%)
```

#### Sección 7 — Top 5 temporeros por horas trabajadas

Tabla con las 5 personas que más horas llevan en los últimos 30 días:

```
--- TOP 5 TEMPOREROS POR HORAS (últimos 30 días) ---
NOMBRE                    HORAS    LABORES
Juan Pérez                142.5       18
María González            138.0       15
...
```

#### Sección 8 — Productividad por cuartel

Tabla con todos los cuarteles ordenados por kilos cosechados (descendente). Incluye hectáreas y productividad (kg/hectárea):

```
--- PRODUCTIVIDAD POR CUARTEL ---
CUARTEL   HECTÁREAS   KILOS TOTAL   KG/HECTÁREA
A-1         5.50       1,245.50        226.45
B-1        12.00       2,890.00        240.83
...
```

#### Sección 9 — Alertas extendidas

Agrega a las alertas del Día 3 las siguientes:

- ⚠️ Temporeros activos sin labores registradas en los últimos 7 días
- ⚠️ Cuarteles activos sin labores registradas en los últimos 7 días
- ⚠️ Temporeros que trabajaron más de 60 horas en la última semana (posible sobrecarga laboral)

### Argumento nuevo de línea de comandos

Agrega al `argparse` un nuevo argumento: `--dias N`. Por defecto vale 30. Permite ajustar el rango temporal del análisis. Ejemplos:

- `python reportes.py --dias 7` → reporte de los últimos 7 días
- `python reportes.py --dias 90` → reporte de los últimos 90 días
- `python reportes.py --solo-activos --dias 15` → combinable con el otro argumento

---

## 📤 Entrega

Tu carpeta `24-04-2026/` debe contener:

```
24-04-2026/
├── proyecto_django/
│   ├── campo/
│   ├── temporeros/
│   │   ├── migrations/
│   │   ├── models.py      ← con los 3 modelos
│   │   └── ...
│   └── manage.py
├── requirements.txt
├── poblar_datos.py
├── consultas_orm.py
└── reportes.py
```

Súbelo con: `git add`, `git commit -m "dia 04 - relaciones entre modelos"`, `git push`.