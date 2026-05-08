# 📘 Tarea 7 — APIViews con Serializers Anidados

---

## 🛠️ Contexto: Taller AutoServicio

El dueño de un taller mecánico en Talca quiere digitalizar su negocio. Hoy maneja todo en papel: clientes, sus vehículos, y las órdenes de trabajo que llegan cada día.

> *"Oye, necesito un sistema donde yo pueda ver un cliente y de una ver todos los autos que ha traído. Y cuando abra una orden de trabajo, quiero ver el auto y el dueño sin tener que buscar en otro lado. No me hagas buscar en cinco pantallas distintas."*

Vas a construir la API de ese sistema desde cero — nuevo proyecto Django, nuevos modelos, nuevos endpoints.

### 📁 Estructura del proyecto

```
Res-Tarea-7/
├── proyecto_django/
│   ├── taller/              ← proyecto Django (reemplaza "campo")
│   │   ├── settings.py
│   │   └── urls.py
│   └── servicio/            ← app principal (reemplaza "temporeros")
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── poblar_datos.py          ← script standalone para poblar la BD
├── pruebas_api.http
├── .env
└── requirements.txt
```

### 📋 Qué vas a entregar

| Archivo | Contenido |
|---------|-----------|
| `servicio/models.py` | 4 modelos con relaciones |
| `servicio/serializers.py` | Serializers planos + anidados |
| `servicio/views.py` | 8 APIViews |
| `poblar_datos.py` | Script que crea datos de prueba |
| `pruebas_api.http` | 15 requests |

---

## 🗃️ Tarea 1: Modelos

📄 **Archivo:** `servicio/models.py`

### Modelo `Mecanico`

| Campo | Tipo | Restricciones |
|-------|------|--------------|
| `nombre` | CharField | max_length=100 |
| `rut` | CharField | max_length=12, unique |
| `especialidad` | CharField | choices: Motor / Electricidad / Carrocería / Frenos / General |
| `activo` | BooleanField | default=True |

`__str__`: `f"{self.nombre} ({self.especialidad})"`

### Modelo `Cliente`

| Campo | Tipo | Restricciones |
|-------|------|--------------|
| `nombre` | CharField | max_length=100 |
| `rut` | CharField | max_length=12, unique |
| `telefono` | CharField | max_length=15, blank=True |
| `email` | EmailField | blank=True |
| `fecha_registro` | DateField | auto_now_add=True |

`__str__`: `f"{self.nombre} ({self.rut})"`

### Modelo `Vehiculo`

| Campo | Tipo | Restricciones |
|-------|------|--------------|
| `patente` | CharField | max_length=8, unique |
| `marca` | CharField | max_length=50 |
| `modelo` | CharField | max_length=50 |
| `anio` | IntegerField | |
| `color` | CharField | max_length=30 |
| `kilometraje` | IntegerField | default=0 |
| `cliente` | ForeignKey | Cliente, on_delete=PROTECT, related_name='vehiculos' |

`__str__`: `f"{self.patente} — {self.marca} {self.modelo} ({self.anio})"`

### Modelo `OrdenTrabajo`

| Campo | Tipo | Restricciones |
|-------|------|--------------|
| `vehiculo` | ForeignKey | Vehiculo, on_delete=PROTECT, related_name='ordenes' |
| `mecanico` | ForeignKey | Mecanico, on_delete=PROTECT, related_name='ordenes' |
| `descripcion` | TextField | |
| `estado` | CharField | choices: Pendiente / En progreso / Completada / Cancelada, default=Pendiente |
| `fecha_ingreso` | DateField | auto_now_add=True |
| `fecha_entrega_estimada` | DateField | |
| `fecha_entrega_real` | DateField | null=True, blank=True |
| `monto` | DecimalField | max_digits=10, decimal_places=2, null=True, blank=True |
| `observaciones` | TextField | blank=True |

`Meta`: `ordering = ['-fecha_ingreso']`

`__str__`: `f"Orden #{self.pk} — {self.vehiculo.patente} ({self.estado})"`

---

## 🔧 Tarea 2: Serializers

📄 **Archivo:** `servicio/serializers.py`

Este es el núcleo del día. Vas a construir serializers en dos niveles: **planos** (solo IDs para escritura) y **anidados** (objetos completos para lectura).

### Concepto: serializer anidado

Cuando el frontend pide el detalle de un cliente, no quiere ver esto:
```json
{
    "id": 1,
    "nombre": "Juan Pérez",
    "vehiculos": [3, 7, 12]
}
```

Quiere ver esto — los objetos completos, sin hacer requests adicionales:
```json
{
    "id": 1,
    "nombre": "Juan Pérez",
    "vehiculos": [
        {"patente": "ABCD12", "marca": "Toyota", "modelo": "Corolla"},
        {"patente": "XY9900", "marca": "Hyundai", "modelo": "Tucson"}
    ]
}
```

Para lograr esto, incluyes un serializer dentro de otro:

```python
class VehiculoResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'patente', 'marca', 'modelo', 'anio', 'color']

class ClienteSerializer(serializers.ModelSerializer):
    vehiculos = VehiculoResumenSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'rut', 'telefono', 'email',
                  'fecha_registro', 'vehiculos']
```

`read_only=True` en el campo anidado significa que DRF lo usa solo para leer — no intenta escribir vehículos cuando haces POST de un cliente.

---

### Serializers que debes implementar

#### `MecanicoSerializer`
Todos los campos. Agrega un campo calculado `total_ordenes` con `SerializerMethodField` que cuente `obj.ordenes.count()`.

#### `ClienteResumenSerializer`
Solo: `id`, `nombre`, `rut`, `telefono`. Sin vehículos. Se usa cuando aparece anidado dentro de otros serializers.

#### `ClienteSerializer`
Todos los campos de `Cliente` + campo `vehiculos` anidado con `VehiculoResumenSerializer`. El campo `vehiculos` es `read_only=True`.

#### `VehiculoResumenSerializer`
Solo: `id`, `patente`, `marca`, `modelo`, `anio`, `color`. Sin ordenes. Se usa cuando aparece anidado dentro de otros serializers.

#### `OrdenResumenSerializer`
Solo: `id`, `estado`, `fecha_ingreso`, `fecha_entrega_estimada`, `monto`. Sin vehículo ni mecánico anidado. Se usa dentro de `VehiculoSerializer`.

#### `VehiculoSerializer`
Todos los campos de `Vehiculo` + campo `cliente` anidado con `ClienteResumenSerializer` + campo `ordenes` anidado con `OrdenResumenSerializer`.

> ⚠️ **Referencia circular:** si `ClienteSerializer` anida `VehiculoSerializer` y `VehiculoSerializer` anida `ClienteSerializer`, tendrías un loop infinito. Por eso usas las versiones "Resumen" que no tienen el campo de vuelta.

#### `OrdenTrabajoSerializer`
Todos los campos de `OrdenTrabajo` + campo `vehiculo` anidado con `VehiculoResumenSerializer` + campo `mecanico` anidado con `MecanicoSerializer`.

#### `OrdenTrabajoCreateSerializer`
Para POST. Solo IDs — no objetos anidados:

```python
class OrdenTrabajoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenTrabajo
        fields = ['vehiculo', 'mecanico', 'descripcion',
                  'fecha_entrega_estimada', 'observaciones']
```

`estado` no va — siempre empieza como `Pendiente`.
`monto` no va — se agrega cuando se completa la orden.

#### `OrdenTrabajoUpdateSerializer`
Para PATCH. Solo los campos que se pueden actualizar:

```python
fields = ['mecanico', 'estado', 'fecha_entrega_estimada',
          'fecha_entrega_real', 'monto', 'observaciones']
```

Implementa `validate()` con esta regla: si `estado == "Completada"` y `monto` es `None` → `raise serializers.ValidationError({"monto": "obligatorio para marcar una orden como Completada"})`.

---

## 🌐 Tarea 3: APIViews

📄 **Archivo:** `servicio/views.py`

Usa el mismo patrón del Día 6: `APIView`, `logger = logging.getLogger('servicio')`, `logger.debug(...)` al inicio de cada método.

---

### View 1 — Lista y creación de mecánicos

**URL:** `GET /api/mecanicos/` y `POST /api/mecanicos/`

**GET — Query params:**
- `?activo=true/false`
- `?especialidad=Motor`

**GET — Respuesta:**
```json
{
    "total": 8,
    "mecanicos": [
        {
            "id": 1,
            "nombre": "Carlos Muñoz",
            "rut": "12345678-9",
            "especialidad": "Motor",
            "activo": true,
            "total_ordenes": 14
        }
    ]
}
```

**POST — Body:**
```json
{
    "nombre": "Pedro Soto",
    "rut": "98765432-1",
    "especialidad": "Frenos"
}
```

**POST — Respuesta 201:**
```json
{
    "mensaje": "Mecánico creado",
    "mecanico": { ... }
}
```

**POST — Error 400** si el RUT ya existe:
```json
{
    "error": "Ya existe un mecánico con el RUT '98765432-1'"
}
```

---

### View 2 — Detalle de mecánico

**URL:** `GET /api/mecanicos/<rut>/`

**Respuesta:**
```json
{
    "mecanico": {
        "id": 1,
        "nombre": "Carlos Muñoz",
        "especialidad": "Motor",
        "total_ordenes": 14
    },
    "ordenes_activas": [
        {
            "id": 5,
            "vehiculo": {"patente": "ABCD12", "marca": "Toyota"},
            "estado": "En progreso",
            "fecha_entrega_estimada": "2026-05-10"
        }
    ],
    "stats": {
        "ordenes_completadas": 10,
        "ordenes_canceladas": 1,
        "monto_total_facturado": 1850000.00
    }
}
```

`ordenes_activas` son las que tienen estado `Pendiente` o `En progreso`.

---

### View 3 — Lista y creación de clientes

**URL:** `GET /api/clientes/` y `POST /api/clientes/`

**GET — Query params:**
- `?buscar=juan` (busca en nombre, case-insensitive)
- `?con_vehiculos=true` (solo clientes que tienen al menos un vehículo)

**GET — Respuesta:** `{total, clientes}` con `vehiculos` anidados usando `ClienteSerializer`.

**POST — Body:** campos de `Cliente` sin `vehiculos`. Respuesta 201 con el cliente creado.

---

### View 4 — Detalle de cliente

**URL:** `GET /api/clientes/<rut>/`

**Respuesta:**
```json
{
    "cliente": {
        "id": 1,
        "nombre": "Juan Pérez",
        "rut": "11111111-1",
        "telefono": "912345678",
        "vehiculos": [
            {
                "patente": "ABCD12",
                "marca": "Toyota",
                "modelo": "Corolla",
                "anio": 2019,
                "color": "Blanco"
            }
        ]
    },
    "stats": {
        "total_vehiculos": 1,
        "total_ordenes": 3,
        "ordenes_activas": 1,
        "monto_total_gastado": 450000.00
    }
}
```

`monto_total_gastado` suma el monto de todas las órdenes completadas de todos sus vehículos. Usa `aggregate()`.

---

### View 5 — Lista y creación de vehículos

**URL:** `GET /api/vehiculos/` y `POST /api/vehiculos/`

**GET — Query params:**
- `?marca=Toyota`
- `?cliente_rut=11111111-1`
- `?anio_desde=2015&anio_hasta=2020`

**GET — Respuesta:** `{total, vehiculos}` con `cliente` anidado (solo `ClienteResumenSerializer`).

**POST — Body:**
```json
{
    "patente": "ABCD12",
    "marca": "Toyota",
    "modelo": "Corolla",
    "anio": 2019,
    "color": "Blanco",
    "kilometraje": 45000,
    "cliente": 1
}
```

El campo `cliente` acepta el ID (entero). Respuesta 201 con el vehículo creado.

---

### View 6 — Detalle de vehículo

**URL:** `GET /api/vehiculos/<patente>/`

**Respuesta:**
```json
{
    "vehiculo": {
        "patente": "ABCD12",
        "marca": "Toyota",
        "modelo": "Corolla",
        "anio": 2019,
        "color": "Blanco",
        "kilometraje": 45000,
        "cliente": {
            "id": 1,
            "nombre": "Juan Pérez",
            "rut": "11111111-1",
            "telefono": "912345678"
        },
        "ordenes": [
            {
                "id": 3,
                "estado": "Completada",
                "fecha_ingreso": "2026-04-10",
                "fecha_entrega_estimada": "2026-04-12",
                "monto": 85000.00
            }
        ]
    },
    "stats": {
        "total_ordenes": 3,
        "ultima_visita": "2026-04-10",
        "monto_total_gastado": 245000.00
    }
}
```

---

### View 7 — Lista y creación de órdenes de trabajo

**URL:** `GET /api/ordenes/` y `POST /api/ordenes/`

**GET — Query params:**
- `?estado=Pendiente`
- `?mecanico_rut=12345678-9`
- `?vehiculo_patente=ABCD12`
- `?vencidas=true` → `fecha_entrega_estimada < hoy` y estado no es `Completada` ni `Cancelada`

**GET — Respuesta:**
```json
{
    "total": 45,
    "ordenes": [
        {
            "id": 3,
            "vehiculo": {
                "patente": "ABCD12",
                "marca": "Toyota",
                "modelo": "Corolla"
            },
            "mecanico": {
                "nombre": "Carlos Muñoz",
                "especialidad": "Motor"
            },
            "estado": "En progreso",
            "fecha_ingreso": "2026-04-10",
            "fecha_entrega_estimada": "2026-04-12",
            "monto": null
        }
    ]
}
```

**POST — Body:**
```json
{
    "vehiculo": 1,
    "mecanico": 1,
    "descripcion": "Cambio de aceite y filtros",
    "fecha_entrega_estimada": "2026-05-10"
}
```

Usa `OrdenTrabajoCreateSerializer`. Respuesta 201 con la orden completa serializada con `OrdenTrabajoSerializer`.

---

### View 8 — Detalle y actualización de una orden

**URL:** `GET /api/ordenes/<id>/` y `PATCH /api/ordenes/<id>/`

**GET — Respuesta:** orden completa con `vehiculo` anidado (incluyendo `cliente`) y `mecanico` anidado.

**PATCH — Body:**
```json
{
    "estado": "Completada",
    "fecha_entrega_real": "2026-05-09",
    "monto": 85000
}
```

Usa `OrdenTrabajoUpdateSerializer`. Si `estado == "Completada"` y falta `monto` → 400. Respuesta 200 con la orden actualizada.

---

## 🌱 Tarea 4: poblar_datos.py

📄 **Archivo:** `Res-Tarea-7/poblar_datos.py`

Script standalone que crea datos de prueba. Debe crear:

- 8 mecánicos (al menos 1 por especialidad, 1 inactivo)
- 20 clientes con RUTs válidos chilenos
- 35 vehículos distribuidos entre los clientes (algunos clientes con más de uno)
- 60 órdenes de trabajo:
  - 15 Pendientes
  - 10 En progreso
  - 30 Completadas (con monto y fecha_entrega_real)
  - 5 Canceladas

**Reglas:**
- Idempotente — si ya existen los datos, no duplica. Usa `get_or_create()`.
- Las fechas de ingreso distribuidas en los últimos 90 días.
- Los montos de órdenes completadas entre $30.000 y $500.000.
- Al final imprime resumen:

```
============================
DATOS CREADOS
============================
Mecánicos:   8
Clientes:   20
Vehículos:  35
Órdenes:    60
  Pendientes:    15
  En progreso:   10
  Completadas:   30
  Canceladas:     5
============================
```

---

## 🧪 Tarea 5: pruebas_api.http

15 requests:

```http
### 1. Lista todos los mecánicos
GET http://localhost:8000/api/mecanicos/

###

### 2. Solo mecánicos de Motor
GET http://localhost:8000/api/mecanicos/?especialidad=Motor

###

### 3. Detalle de mecánico con stats
GET http://localhost:8000/api/mecanicos/<rut>/

###

### 4. Crear mecánico válido → 201
POST http://localhost:8000/api/mecanicos/
Content-Type: application/json

{"nombre": "Ana López", "rut": "...", "especialidad": "Electricidad"}

###

### 5. Crear mecánico con RUT duplicado → 400
POST http://localhost:8000/api/mecanicos/
Content-Type: application/json

{"nombre": "Otro", "rut": "<rut_que_ya_existe>", "especialidad": "General"}

###

### 6. Lista clientes con vehículos anidados
GET http://localhost:8000/api/clientes/

###

### 7. Solo clientes con vehículos
GET http://localhost:8000/api/clientes/?con_vehiculos=true

###

### 8. Detalle de cliente con stats
GET http://localhost:8000/api/clientes/<rut>/

###

### 9. Vehículos marca Toyota
GET http://localhost:8000/api/vehiculos/?marca=Toyota

###

### 10. Detalle de vehículo con cliente y órdenes anidados
GET http://localhost:8000/api/vehiculos/<patente>/

###

### 11. Órdenes pendientes
GET http://localhost:8000/api/ordenes/?estado=Pendiente

###

### 12. Órdenes vencidas
GET http://localhost:8000/api/ordenes/?vencidas=true

###

### 13. Crear orden válida → 201
POST http://localhost:8000/api/ordenes/
Content-Type: application/json

{"vehiculo": 1, "mecanico": 1, "descripcion": "Cambio aceite", "fecha_entrega_estimada": "2026-05-15"}

###

### 14. Completar orden con monto → 200
PATCH http://localhost:8000/api/ordenes/<id>/
Content-Type: application/json

{"estado": "Completada", "fecha_entrega_real": "2026-05-09", "monto": 85000}

###

### 15. Completar orden sin monto → 400
PATCH http://localhost:8000/api/ordenes/<id>/
Content-Type: application/json

{"estado": "Completada"}
```

Completa los `<rut>`, `<patente>` e `<id>` con valores reales de tu BD antes de ejecutar.

---

## 🚨 Reglas obligatorias

1. **Serializers separados para lectura y escritura.** Los serializers con objetos anidados son `read_only`. Para POST/PATCH usas serializers con IDs.
2. **Sin referencias circulares.** Si A anida B y B anida A → uno usa la versión resumen del otro.
3. **`select_related` en los querysets** que acceden a relaciones. Si tienes `orden.vehiculo.cliente.nombre` en un serializer sin `select_related`, estás haciendo N+1 queries. Investiga `queryset.select_related('vehiculo__cliente', 'mecanico')`.
4. **Errores siempre en JSON.** Nunca HTML de Django.
5. **Logger** en cada método.
6. **`.env` con las credenciales** — mismo patrón que el Día 6.

---

## ✅ Verificaciones antes del commit

- [ ] `python poblar_datos.py` crea los datos sin errores y es idempotente.
- [ ] `GET /api/clientes/<rut>/` devuelve vehículos como objetos, no como IDs.
- [ ] `GET /api/vehiculos/<patente>/` devuelve cliente anidado con nombre y rut.
- [ ] `GET /api/ordenes/<id>/` devuelve vehículo anidado Y mecánico anidado.
- [ ] `POST /api/ordenes/` acepta IDs en `vehiculo` y `mecanico`, no objetos.
- [ ] `PATCH /api/ordenes/<id>/` con estado=Completada sin monto devuelve 400.
- [ ] `GET /api/ordenes/?vencidas=true` devuelve solo las atrasadas.
- [ ] Las 15 requests del `.http` tienen el código correcto anotado.

---

## 📤 Entrega

```
Res-Tarea-7/
├── proyecto_django/
│   ├── taller/
│   │   ├── settings.py
│   │   └── urls.py
│   └── servicio/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── poblar_datos.py
├── pruebas_api.http
└── requirements.txt
```

`git add`, `git commit -m "dia 07 - taller mecanico serializers anidados"`, `git push`.