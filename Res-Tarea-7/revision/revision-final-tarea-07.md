# 📋 Revisión Final — Tarea 7 (Re-entrega)

Auditoría en vivo sobre el contenedor `terrasoft_test` (Postgres 17, puerto 5431), con `.env` temporal de trabajo creado solo para verificar y borrado al final.

---

## ✅ Lo que arreglaste

Los fixes críticos y casi todos los graves de la revisión anterior están aplicados y verificados en vivo:

- **C1.** `ClienteListView` ahora tiene `post()` y los filtros `?buscar=` y `?con_vehiculos=true` funcionan. Verificado: sin filtro `total=21`, `?buscar=Juan` → `total=1`, `?con_vehiculos=true` → `total=20`.
- **C2.** `VehiculoListView.post()` implementado. `POST /api/vehiculos/` → 201 con el vehículo creado y `cliente` anidado.
- **C3.** `fecha_ingreso` ya no usa `auto_now_add=True`. Migración `0002_alter_ordentrabajo_fecha_ingreso` aplicada. `poblar_datos.py` distribuye las fechas: `MIN=2026-02-12`, `MAX=2026-05-11`. Como consecuencia, `GET /api/ordenes/?vencidas=true` devuelve 25 órdenes reales, no 0.
- **C4.** `poblar_datos.py` es idempotente con `get_or_create()`. Run 1 y run 2 imprimen los mismos conteos exactos: 8 / 20 / 35 / 60 con distribución 15/10/30/5.
- **G6.** `ClienteDetailView.stats` contiene exactamente los 4 campos pedidos, con `monto_total_gastado`.
- **G7.** `VehiculoResumenSerializer` expone `"anio"` sin tilde.
- **G8.** El resumen de `poblar_datos.py` tiene el formato exacto de la spec.
- **M9, M10, M11.** Monto mínimo 30.000, ruta de detalle de orden con `<int:id>`, RUT real en request #4.

Las regresiones de modelos, serializers anidados, `validate()` de Completada, `total_ordenes` y `logger.debug()` siguen en orden. `prefetch_related('vehiculos__ordenes')` en `ClienteDetailView` está bien — la revisión anterior pedía `select_related` ahí por error; para reverse FK (cliente → vehiculos) Django requiere `prefetch_related`.

---

## ❌ Lo que falta corregir

### 🟡 Graves

#### 1. No existe `Res-Tarea-7/.env.example` (proyecto no arranca al clonar)

Sin `.env`, el proyecto no arranca: `decouple` lanza `UndefinedValueError: SECRET_KEY not found`. La spec pide que el proyecto sea reproducible. Para auditar tuve que crear un `.env` temporal y borrarlo después.

`.env` debe seguir fuera del repo (credenciales locales), pero necesitas un `.env.example` trackeado para que quien clone el repo pueda copiarlo y arrancar:

```bash
# Res-Tarea-7/.env.example
SECRET_KEY=cambia-esto-en-tu-local
DEBUG=True
DB_NAME=terrasoft_2026
DB_USER=admin
DB_PASSWORD=admin123
DB_HOST=localhost
DB_PORT=5431
```

Flujo para quien clone:

```bash
cp .env.example .env
# editar .env si hace falta
```

Verifica que `.env.example` esté trackeado (no en `.gitignore`) y que `.env` siga ignorado.

#### 2. `REST_FRAMEWORK` incluye `BrowsableAPIRenderer`

En `settings.py` línea 130. La spec pide solo `JSONRenderer` y `JSONParser`. `BrowsableAPIRenderer` puede devolver HTML cuando el cliente envía `Accept: text/html` (un navegador), lo que rompe la regla "errores siempre en JSON".

```diff
 REST_FRAMEWORK = {
     'DEFAULT_RENDERER_CLASSES': [
         'rest_framework.renderers.JSONRenderer',
-        'rest_framework.renderers.BrowsableAPIRenderer',
     ],
     'DEFAULT_PARSER_CLASSES': [
         'rest_framework.parsers.JSONParser',
     ],
 }
```

#### 3. 404 a ruta inexistente devuelve HTML (no JSON)

Hallazgo nuevo de la pasada en vivo. `GET /api/inexistente/` responde:

```
HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8

<!DOCTYPE html><html lang="en">... Page not found at /api/inexistente/...
```

Tus views devuelven JSON cuando el objeto no existe (404 controlado), pero cuando la URL completa no matchea ningún `path()`, Django sirve la página HTML de error. Esto contradice la regla de spec: "Errores siempre en JSON. Nunca HTML de Django."

**Fix:** define un handler 404 global en `taller/urls.py`:

```python
# taller/urls.py
from django.http import JsonResponse

def handler_404(request, exception):
    return JsonResponse(
        {"error": f"Recurso no encontrado: {request.path}"},
        status=404,
    )

handler404 = "taller.urls.handler_404"
```

Y asegúrate de que `DEBUG=False` en producción — con `DEBUG=True` Django siempre muestra su página de debug en lugar del handler. Para verificar el fix en desarrollo, prueba con `DEBUG=False` y `ALLOWED_HOSTS=['localhost']` puntualmente.

### 🟢 Menores

#### 4. Ruta extra `estadisticas/`

`servicio/urls.py` línea 23 registra `path('estadisticas/', views.EstadisticasView.as_view())` y la clase vive en `views.py` línea 584. La spec define 8 rutas, no 9. Esto ya estaba pendiente desde la entrega anterior.

```diff
# servicio/urls.py
-    path('estadisticas/', views.EstadisticasView.as_view()),
```

Y borra `EstadisticasView` de `views.py`.

---

## 📋 Resumen de cambios

| Archivo | Cambio |
|---------|--------|
| `Res-Tarea-7/.env.example` | Crear y trackear con valores dummy de `SECRET_KEY`, `DEBUG`, `DB_*` |
| `Res-Tarea-7/.env` | Crear local (no trackeado) copiando del example |
| `taller/settings.py` | Quitar `BrowsableAPIRenderer` de `REST_FRAMEWORK` |
| `taller/urls.py` | Agregar `handler_404` que retorne JSON |
| `servicio/urls.py` | Quitar ruta `estadisticas/` |
| `servicio/views.py` | Quitar clase `EstadisticasView` |

---

## ✅ Verificaciones en vivo que pasaron

Para que veas que la entrega base está sana — todo esto se probó con la BD real:

| # | Verificación | Resultado |
|---|--------------|-----------|
| 1 | `manage.py check` | OK |
| 2 | `manage.py migrate` | OK |
| 3 | `poblar_datos.py` corrido 2 veces | Idempotente |
| 4 | `GET /api/ordenes/?vencidas=true` | 200, 25 órdenes |
| 5 | `POST /api/clientes/` | 201 |
| 6 | `POST /api/vehiculos/` | 201 |
| 7 | `GET /api/clientes/<rut>/` stats correcto | 200 |
| 8 | `GET /api/vehiculos/<patente>/` con `"anio"` | 200 |
| 9 | Filtros de clientes (`buscar`, `con_vehiculos`) | OK |
| 10 | `PATCH /api/ordenes/<id>/` Completada sin monto | 400 |

---

## 📤 Entrega

```bash
cd Res-Tarea-7

# 1. Crear .env.example (trackeado) y .env (local, no trackeado)
# 2. Editar settings.py, urls.py, views.py según los fixes arriba

git add .env.example
git add proyecto_django/taller/settings.py
git add proyecto_django/taller/urls.py
git add proyecto_django/servicio/urls.py
git add proyecto_django/servicio/views.py

git commit -m "tarea 07 - env.example, fix renderers, handler 404 json, quita ruta extra"
git push
```