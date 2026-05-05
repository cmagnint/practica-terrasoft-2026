# 📘 Tarea 6 — Django REST Framework: tu primer backend con endpoints

---

## 🛠️ Antes de empezar: qué vamos a hacer

Hasta ahora Django te sirvió para modelar datos y correr scripts. Hoy vas a convertirlo en un **servidor HTTP real** — uno que recibe requests desde un navegador o un frontend y devuelve JSON.

Este es el concepto central del día:

```
Frontend (Next.js, curl, .http)
        │
        │  HTTP Request  →  GET /api/temporeros/
        ▼
   Django + DRF
        │  Consulta ORM → BD PostgreSQL
        │  Serializa datos → JSON
        │
        │  HTTP Response  →  200 OK + JSON
        ▼
Frontend recibe los datos y los muestra
```

Al final del día vas a tener una API funcionando con 7 endpoints, vas a saber leer los logs del servidor mientras recibe requests, y vas a entender qué pasa exactamente entre que el frontend pide un dato y lo recibe.

**Reutilizas el proyecto Django de Res-Tarea-5.** Copia la carpeta a `Res-Tarea-6/`.

### 📁 Estructura que debes crear

```
Res-Tarea-6/
├── proyecto_django/
│   ├── campo/
│   │   ├── settings.py      ← agregar DRF y configuración de logs
│   │   └── urls.py          ← registrar rutas de la API
│   └── temporeros/
│       ├── serializers.py   ← NUEVO
│       ├── views.py         ← reemplazar con APIViews
│       └── urls.py          ← NUEVO
├── pruebas_api.http          ← archivo para REST Client de VS Code
├── logs_anotados.md          ← análisis de logs del servidor
└── requirements.txt          ← agregar djangorestframework
```

### 📋 Qué vas a entregar

| Archivo | Contenido | ¿Es obligatorio? |
|---------|-----------|------------------|
| `temporeros/serializers.py` | 4 serializers | ✅ Sí |
| `temporeros/views.py` | 6 clases APIView | ✅ Sí |
| `temporeros/urls.py` | Rutas de la app | ✅ Sí |
| `campo/urls.py` | Rutas globales actualizadas | ✅ Sí |
| `campo/settings.py` | DRF instalado + logging configurado | ✅ Sí |
| `pruebas_api.http` | 12 requests con REST Client | ✅ Sí |
| `logs_anotados.md` | 5 logs reales copiados y analizados | ✅ Sí |
| `requirements.txt` | Incluye `djangorestframework` | ✅ Sí |

---

## ⚙️ Tarea 1: Instalar y configurar DRF

### 1️⃣ Instalar

```bash
pip install djangorestframework
```

Agrega al `requirements.txt`.

### 2️⃣ Registrar en `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'temporeros',
]
```

### 3️⃣ Configuración de DRF en `settings.py`

Agrega este bloque al final:

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
```

> 💡 `JSONRenderer` hace que la API devuelva JSON puro. Sin esto, DRF también devuelve una interfaz web navegable (HTML) — útil para explorar pero queremos JSON solamente.

### 4️⃣ Configurar logging en `settings.py`

Agrega este bloque. Hace que el servidor imprima en consola cada request con su código de respuesta:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} — {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'temporeros': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 5️⃣ Crear `temporeros/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # se completa en Tarea 3
]
```

### 6️⃣ Actualizar `campo/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('temporeros.urls')),
]
```

---

## 🔧 Tarea 2: Serializers

📄 **Archivo:** `temporeros/serializers.py`

Un serializer convierte un objeto del ORM en un diccionario Python que luego se transforma en JSON. También valida datos de entrada en endpoints POST.

### TemporeroSerializer

```python
from rest_framework import serializers
from .models import Temporero

class TemporeroSerializer(serializers.ModelSerializer):
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Temporero
        fields = [
            'id', 'nombre', 'rut', 'telefono', 'contacto_emergencia',
            'fecha_ingreso', 'supervisor', 'fecha_nacimiento', 'talla_polera',
            'activo', 'edad',
        ]

    def get_edad(self, obj):
        from datetime import date
        hoy = date.today()
        return hoy.year - obj.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
        )
```

`SerializerMethodField` es un campo calculado — no existe en la BD, se calcula al serializar. `get_edad` es la función que DRF busca automáticamente por nombre (`get_<nombre_campo>`).

### CuartelSerializer

Serializa todos los campos del modelo `Cuartel`. Agrega un campo calculado `cantidad_labores` que cuente cuántas labores tiene ese cuartel en total usando `obj.labores.count()` (el `related_name` que definiste en el modelo).

### LaborSerializer

Serializa todos los campos de `Labor`. Agrega dos campos calculados:
- `temporero_nombre`: `obj.temporero.nombre`
- `cuartel_nombre`: `obj.cuartel.nombre`

> ⚠️ Los `DecimalField` se serializan como string por defecto (`"8.50"`). El frontend necesita números. Investiga cómo forzar `coerce_to_string=False` en DRF.

### LaborCreateSerializer

Serializer separado para POST. Solo incluye los campos que el frontend envía — sin campos calculados:

```python
class LaborCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Labor
        fields = ['temporero', 'cuartel', 'tipo', 'fecha',
                  'horas_trabajadas', 'kilos_cosechados', 'observaciones']

    def validate(self, data):
        ...
        return data
```

Implementa `validate()` con estas reglas:
- Si `tipo != "Cosecha"` y `kilos_cosechados` tiene valor → `raise serializers.ValidationError({"kilos_cosechados": "solo aplica para tipo Cosecha"})`
- Si `tipo == "Cosecha"` y `kilos_cosechados` es `None` → error: `"obligatorio para tipo Cosecha"`
- Si `horas_trabajadas <= 0` o `horas_trabajadas > 12` → error: `"debe estar entre 0 y 12"`

---

## 🌐 Tarea 3: APIViews y URLs

📄 **Archivo:** `temporeros/views.py`

Vas a construir 6 clases usando `APIView`. Esta clase te da control total sobre qué pasa con cada método HTTP.

Estructura base:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('temporeros')

class MiView(APIView):

    def get(self, request):
        logger.debug(f"GET {request.path} — params: {request.query_params}")
        data = ...
        return Response(data, status=status.HTTP_200_OK)
```

> 💡 Si la view no define `post()`, DRF responde automáticamente con `405 Method Not Allowed`. No tienes que manejar esto tú.

---

### View 1 — Lista de temporeros

**Clase:** `TemporeroListView`
**URL:** `GET /api/temporeros/`

**Query params opcionales (todos combinables):**

| Param | Ejemplo | Descripción |
|-------|---------|-------------|
| `activo` | `?activo=true` | Filtra activos/inactivos |
| `supervisor` | `?supervisor=true` | Solo supervisores |
| `talla` | `?talla=XL` | Filtra por talla |
| `buscar` | `?buscar=juan` | Busca en nombre (case-insensitive) |

**Respuesta 200:**
```json
{
    "total": 27,
    "temporeros": [
        {
            "id": 1,
            "nombre": "Juan Pérez",
            "rut": "11111111-1",
            "telefono": "912345678",
            "contacto_emergencia": "María Pérez",
            "fecha_ingreso": "2026-03-01",
            "supervisor": true,
            "fecha_nacimiento": "1985-06-15",
            "talla_polera": "L",
            "activo": true,
            "edad": 40
        }
    ]
}
```

---

### View 2 — Detalle de un temporero

**Clase:** `TemporeroDetailView`
**URL:** `GET /api/temporeros/<rut>/`

`<rut>` es el RUT normalizado: `11111111-1`.

**Respuesta 200:**
```json
{
    "temporero": { ... },
    "labores_recientes": [
        {
            "id": 5,
            "cuartel_nombre": "A-1",
            "tipo": "Cosecha",
            "fecha": "2026-04-05",
            "horas_trabajadas": 8.0,
            "kilos_cosechados": 95.5,
            "observaciones": ""
        }
    ],
    "stats": {
        "total_labores": 23,
        "total_horas": 184.5,
        "total_kilos_cosechados": 987.3,
        "tipos_realizados": ["Cosecha", "Poda", "Riego"]
    }
}
```

`labores_recientes` son las últimas 10 ordenadas por fecha descendente.

**Respuesta 404:**
```json
{
    "error": "Temporero con RUT '99999999-9' no encontrado"
}
```

---

### View 3 — Lista de cuarteles

**Clase:** `CuartelListView`
**URL:** `GET /api/cuarteles/`

**Query params:** `?activo=true`, `?variedad=Legacy`

**Respuesta 200:**
```json
{
    "total": 46,
    "cuarteles": [
        {
            "id": 1,
            "nombre": "A-1",
            "hectareas": 5.75,
            "variedad": "Duke",
            "activo": true,
            "cantidad_labores": 87
        }
    ]
}
```

---

### View 4 — Detalle de un cuartel

**Clase:** `CuartelDetailView`
**URL:** `GET /api/cuarteles/<nombre>/`

**Respuesta 200:**
```json
{
    "cuartel": { ... },
    "productividad": {
        "total_kilos_cosechados": 2890.5,
        "total_horas_trabajadas": 345.0,
        "kg_por_hectarea": 502.7,
        "cantidad_cosechas": 45,
        "temporeros_distintos": 18
    },
    "labores_por_tipo": {
        "Cosecha": 45,
        "Poda": 12,
        "Riego": 8,
        "Pesticida": 3,
        "Limpieza": 5
    }
}
```

Usa `aggregate()` y `annotate()` del ORM para calcular `productividad`. No iteres fila por fila.

**Respuesta 404:**
```json
{
    "error": "Cuartel 'Z-99' no encontrado"
}
```

---

### View 5 — Lista y creación de labores

**Clase:** `LaborView`
**URL:** `GET /api/labores/` y `POST /api/labores/`

**GET — Query params:**

| Param | Ejemplo | Descripción |
|-------|---------|-------------|
| `tipo` | `?tipo=Cosecha` | Filtra por tipo |
| `cuartel` | `?cuartel=A-1` | Filtra por nombre de cuartel |
| `temporero_rut` | `?temporero_rut=11111111-1` | Filtra por RUT |
| `desde` | `?desde=2026-03-30` | Fecha desde (inclusive) |
| `hasta` | `?hasta=2026-04-05` | Fecha hasta (inclusive) |
| `limite` | `?limite=50` | Máximo registros a devolver (default 100, max 500) |

**GET — Respuesta 200:**
```json
{
    "total": 1634,
    "mostrando": 100,
    "aviso": "mostrando 100 de 1634 — usa ?limite=N para ver más",
    "labores": [ ... ]
}
```

**POST — Body:**
```json
{
    "temporero": 1,
    "cuartel": 1,
    "tipo": "Cosecha",
    "fecha": "2026-05-06",
    "horas_trabajadas": 8.0,
    "kilos_cosechados": 95.5,
    "observaciones": "Turno mañana"
}
```

**POST — Respuesta 201:**
```json
{
    "mensaje": "Labor creada correctamente",
    "labor": { ... }
}
```

**POST — Respuesta 400:**
```json
{
    "errores": {
        "kilos_cosechados": ["obligatorio para tipo Cosecha"]
    }
}
```

**POST — Respuesta 409 (duplicado):**
```json
{
    "error": "Ya existe una labor de tipo Cosecha para este temporero en el cuartel A-1 el 2026-05-06"
}
```

Implementación del POST:
```python
from django.db import IntegrityError

def post(self, request):
    logger.debug(f"POST /api/labores/ — body: {request.data}")
    serializer = LaborCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'errores': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        labor = serializer.save()
        return Response(
            {'mensaje': 'Labor creada correctamente', 'labor': LaborSerializer(labor).data},
            status=status.HTTP_201_CREATED
        )
    except IntegrityError:
        return Response({'error': '...'}, status=status.HTTP_409_CONFLICT)
```

---

### View 6 — Resumen general

**Clase:** `ResumenView`
**URL:** `GET /api/resumen/`

**Respuesta 200:**
```json
{
    "temporeros": {
        "activos": 410,
        "inactivos": 45,
        "supervisores": 62
    },
    "cuarteles": {
        "activos": 46,
        "total_hectareas": 412.5
    },
    "labores": {
        "total": 1634,
        "fecha_inicio": "2026-03-30",
        "fecha_fin": "2026-04-05",
        "total_horas": 9876.5,
        "total_kilos_cosechados": 89432.3,
        "por_tipo": {
            "Cosecha": 820,
            "Poda": 280,
            "Riego": 210,
            "Pesticida": 180,
            "Limpieza": 144
        }
    }
}
```

Solo ORM. Usa `aggregate()` y `values('tipo').annotate(count=Count('id'))`.

---

### URLs en `temporeros/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('temporeros/', views.TemporeroListView.as_view()),
    path('temporeros/<str:rut>/', views.TemporeroDetailView.as_view()),
    path('cuarteles/', views.CuartelListView.as_view()),
    path('cuarteles/<str:nombre>/', views.CuartelDetailView.as_view()),
    path('labores/', views.LaborView.as_view()),
    path('resumen/', views.ResumenView.as_view()),
]
```

---

## 🪵 Tarea 4: Leer los logs del servidor

Con `python manage.py runserver` corriendo, haz estas 5 requests y anota exactamente lo que aparece en la consola para cada una.

| # | Request | Código esperado |
|---|---------|-----------------|
| 1 | `GET /api/temporeros/` | 200 |
| 2 | `GET /api/temporeros/99999999-9/` | 404 |
| 3 | `POST /api/temporeros/` (sin body) | 405 |
| 4 | `POST /api/labores/` con `{}` | 400 |
| 5 | `GET /api/resumen/` | 200 |

📄 **Archivo:** `logs_anotados.md`

Para cada request documenta esto:

```markdown
## Request N: GET /api/temporeros/99999999-9/

Log copiado de la consola:
[2026-05-06 10:31:44] INFO django.server — "GET /api/temporeros/99999999-9/ HTTP/1.1" 404 52

Qué significa cada parte:
- `2026-05-06 10:31:44` → timestamp de cuando llegó la request
- `GET` → método HTTP usado por el cliente
- `/api/temporeros/99999999-9/` → el path que pidió
- `HTTP/1.1` → versión del protocolo
- `404` → código de respuesta (el RUT no existe en BD)
- `52` → bytes devueltos (tamaño del JSON de error)

¿Qué diferencia un 200 de un 404 en el log?
...
```

El log del punto 4 (POST con body vacío) va a incluir también una línea de tu `logger.debug(...)`. Explica por qué aparece antes de la línea del servidor.

---

## 🧪 Tarea 5: Archivo de pruebas

📄 **Archivo:** `pruebas_api.http`

Instala la extensión **REST Client** en VS Code (autor: Huachao Mao). Crea el archivo con estas 12 requests:

```http
### 1. Lista todos los temporeros
GET http://localhost:8000/api/temporeros/
Content-Type: application/json

###

### 2. Solo supervisores activos
GET http://localhost:8000/api/temporeros/?activo=true&supervisor=true
Content-Type: application/json

###

### 3. Buscar por nombre
GET http://localhost:8000/api/temporeros/?buscar=juan
Content-Type: application/json

###

### 4. Detalle temporero existente
GET http://localhost:8000/api/temporeros/11111111-1/
Content-Type: application/json

###

### 5. Detalle temporero inexistente → 404
GET http://localhost:8000/api/temporeros/99999999-9/
Content-Type: application/json

###

### 6. Cuarteles variedad Legacy
GET http://localhost:8000/api/cuarteles/?variedad=Legacy
Content-Type: application/json

###

### 7. Detalle cuartel A-1
GET http://localhost:8000/api/cuarteles/A-1/
Content-Type: application/json

###

### 8. Labores Cosecha en rango de fechas
GET http://localhost:8000/api/labores/?tipo=Cosecha&desde=2026-03-30&hasta=2026-04-05
Content-Type: application/json

###

### 9. Resumen general
GET http://localhost:8000/api/resumen/
Content-Type: application/json

###

### 10. Crear labor válida → 201
POST http://localhost:8000/api/labores/
Content-Type: application/json

{
    "temporero": 1,
    "cuartel": 1,
    "tipo": "Cosecha",
    "fecha": "2026-05-06",
    "horas_trabajadas": 8.0,
    "kilos_cosechados": 95.5,
    "observaciones": "Prueba REST Client"
}

###

### 11. Cosecha sin kilos → 400
POST http://localhost:8000/api/labores/
Content-Type: application/json

{
    "temporero": 1,
    "cuartel": 1,
    "tipo": "Cosecha",
    "fecha": "2026-05-06",
    "horas_trabajadas": 8.0
}

###

### 12. Método no permitido → 405
POST http://localhost:8000/api/temporeros/
Content-Type: application/json

{}
```

Ejecuta cada una y anota el código de respuesta recibido junto al `###`.

---

## 🔁 Equivalencia curl

Debes saber usar también curl. Estos son los equivalentes de los casos más importantes:

```bash
# Lista supervisores activos
curl "http://localhost:8000/api/temporeros/?supervisor=true" | python3 -m json.tool

# Detalle de cuartel
curl http://localhost:8000/api/cuarteles/A-1/ | python3 -m json.tool

# Ver headers de la respuesta (código HTTP, Content-Type, etc.)
curl -i http://localhost:8000/api/resumen/

# POST crear labor
curl -X POST http://localhost:8000/api/labores/ \
     -H "Content-Type: application/json" \
     -d '{"temporero": 1, "cuartel": 1, "tipo": "Cosecha", "fecha": "2026-05-06", "horas_trabajadas": 8.0, "kilos_cosechados": 95.5}'

# POST inválido (método no permitido)
curl -X POST http://localhost:8000/api/temporeros/ \
     -H "Content-Type: application/json" \
     -d '{}'
```

> 💡 `| python3 -m json.tool` formatea el JSON para que sea legible. Sin él, curl imprime todo en una línea.

---

## 🚨 Reglas obligatorias del día

1. **Sin funciones sueltas en `views.py`.** Todo es una clase que hereda de `APIView`.
2. **Cada view loggea al menos una línea** con `logger.debug(...)` al inicio del método.
3. **Códigos HTTP correctos:** 200 éxito, 201 creación, 400 validación, 404 no existe, 405 método no permitido, 409 duplicado.
4. **Los errores siempre son JSON** — nunca texto plano, nunca HTML de Django.
5. **Serializers separados:** `LaborSerializer` para lectura, `LaborCreateSerializer` para escritura.

---

## ✅ Verificaciones antes del commit

- [ ] `python manage.py runserver` arranca sin errores.
- [ ] `GET /api/temporeros/` devuelve JSON con `total` y lista.
- [ ] `GET /api/temporeros/?supervisor=true` devuelve solo supervisores.
- [ ] `GET /api/temporeros/99999999-9/` devuelve JSON `{"error": "..."}` con código 404, no HTML de Django.
- [ ] `POST /api/temporeros/` devuelve `405 Method Not Allowed` en JSON.
- [ ] `POST /api/labores/` con body válido devuelve `201 Created` con la labor.
- [ ] `POST /api/labores/` con Cosecha sin kilos devuelve `400` con detalle del campo.
- [ ] `GET /api/resumen/` devuelve las 3 secciones (temporeros, cuarteles, labores).
- [ ] Las 12 requests del `.http` muestran el código correcto al ejecutarlas.
- [ ] `logs_anotados.md` tiene los 5 logs reales copiados de consola y analizados.
- [ ] La consola del servidor muestra una línea por cada request recibida.

---

## 📤 Entrega

```
Res-Tarea-6/
├── proyecto_django/
│   ├── campo/
│   │   ├── settings.py
│   │   └── urls.py
│   └── temporeros/
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── pruebas_api.http
├── logs_anotados.md
└── requirements.txt
```

`git add`, `git commit -m "dia 06 - endpoints DRF con APIView"`, `git push`.