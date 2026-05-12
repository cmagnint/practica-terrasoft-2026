# 📋 Revisión Tarea 7 — APIViews con Serializers Anidados

---

## ✅ Lo que está bien

**El núcleo conceptual del día funciona correctamente.** Los serializers anidados están bien implementados — al pedir un cliente se ven los vehículos como objetos completos, al pedir un vehículo se ve el cliente como objeto, y no hay referencias circulares. La separación Resumen vs Completo es correcta.

Los 4 modelos están bien definidos, con FKs PROTECT y `related_name` correctos. Los serializers de Orden (Create y Update) están separados como pide la spec y la validación de `Completada` sin monto funciona. El uso de `select_related` está presente en los querysets con relaciones. Los endpoints de Mecánicos y Órdenes (lista y detalle) están completos.

---

## ❌ Lo que debes corregir

### 🔴 Críticos (rompen funcionalidad)

#### 1. `ClienteListView` no tiene POST ni filtros

Hoy `POST /api/clientes/` devuelve 405. La spec pide creación de clientes. Implementa el método `post()` en la view.

Además, los filtros `?buscar=` y `?con_vehiculos=true` no están implementados — el endpoint devuelve los 20 clientes sin filtrar. Agrega esos filtros en el `get()`.

#### 2. `VehiculoListView` no tiene POST

Mismo problema. `POST /api/vehiculos/` devuelve 405. Implementa `post()` que acepte el ID del cliente y cree el vehículo.

#### 3. `fecha_ingreso` con `auto_now_add=True` rompe `?vencidas=true`

El modelo `OrdenTrabajo` tiene `fecha_ingreso = DateField(auto_now_add=True)`. Esto hace que **todas** las órdenes queden con la fecha del día en que se crearon. Por eso `poblar_datos.py` no puede distribuir las fechas en los últimos 90 días — Django ignora cualquier valor que le pases.

Consecuencia: `GET /api/ordenes/?vencidas=true` siempre devuelve 0 resultados, porque ninguna orden tiene fecha pasada.

**Solución:**
1. Quita `auto_now_add=True` del campo `fecha_ingreso`.
2. Crea la migración: `python manage.py makemigrations`.
3. En `poblar_datos.py`, asigna fechas distribuidas en los últimos 90 días manualmente.
4. En `OrdenTrabajoCreateSerializer` o en la view, asigna `fecha_ingreso = date.today()` cuando se crea por la API.

#### 4. `poblar_datos.py` no es idempotente

Hoy hace `delete()` + `create()`. La spec pide `get_or_create()` — si vuelves a correr el script no debe duplicar datos ni borrar los existentes. Refactoriza usando `get_or_create()` para los 4 modelos.

---

### 🟡 Graves (spec incompleta)

#### 5. `settings.py` incompleto

Faltan tres cosas:

- **Bloque `REST_FRAMEWORK`** con `JSONRenderer` y `JSONParser` (igual que el Día 6).
- **Bloque `LOGGING`** con el logger `'servicio'` (igual que el Día 6 pero con el nombre del app actual).
- **`SECRET_KEY` y `DEBUG`** están hardcodeados — deben leerse desde `.env` igual que las credenciales de BD. Crea el archivo `.env` con todas las variables.

#### 6. `ClienteDetailView.stats` mal armado

Hoy devuelve `total_vehiculos`, `total_ordenes`, `monto_total_facturado`. La spec pide:

```json
"stats": {
    "total_vehiculos": ...,
    "total_ordenes": ...,
    "ordenes_activas": ...,
    "monto_total_gastado": ...
}
```

Cambios: agrega `ordenes_activas` (count de órdenes con estado Pendiente o En progreso) y renombra `monto_total_facturado` → `monto_total_gastado`.

#### 7. `VehiculoResumenSerializer` expone `"año"` en vez de `"anio"`

Esto rompe el contrato JSON. Cualquier frontend que consuma esta API esperando `anio` (que es el nombre del campo en el modelo) va a fallar. Quita el alias y deja que el serializer use el nombre del campo tal cual.

#### 8. Resumen de `poblar_datos.py` no tiene el formato pedido

La spec muestra exactamente:
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

Hoy solo imprime mensajes de progreso simples. Reemplaza por este formato.

---

### 🟢 Menores

**9.** Monto mínimo en `poblar_datos.py` es $50.000. La spec pide $30.000. Cambia el `random.randint`.

**10.** La ruta de detalle de orden usa `<int:pk>` en vez de `<int:id>`. Cámbialo para mantener consistencia con la spec.

**11.** Request #4 en `pruebas_api.http` tiene `"rut": "..."` sin completar. Pon un RUT real.

---

## 📋 Resumen de cambios

| Archivo | Estado | Cambios requeridos |
|---------|--------|--------------------| 
| `servicio/views.py` | ❌ Fix | POST en ClienteList y VehiculoList, filtros de Cliente, stats correcto en ClienteDetail |
| `servicio/models.py` | ❌ Fix | Quitar `auto_now_add` en `fecha_ingreso` |
| `servicio/serializers.py` | ❌ Fix | Quitar alias `"año"` en VehiculoResumenSerializer |
| `taller/settings.py` | ❌ Fix | Agregar REST_FRAMEWORK, LOGGING, SECRET_KEY/DEBUG desde `.env` |
| `.env` | ❌ Crear | Todas las variables (SECRET_KEY, DEBUG, DB_*) |
| `poblar_datos.py` | ❌ Fix | `get_or_create()`, fechas distribuidas, formato del resumen, monto mínimo $30k |
| `servicio/urls.py` | ⚠️ Fix menor | `<int:id>` en detalle de orden |
| `pruebas_api.http` | ⚠️ Fix menor | Completar el RUT en request #4 |
| Migraciones | ❌ Crear | Una nueva por el cambio en `fecha_ingreso` |

---

## 📤 Entrega

```bash
cd Res-Tarea-7/proyecto_django
python manage.py makemigrations
python manage.py migrate

cd ..
git add proyecto_django/servicio/models.py
git add proyecto_django/servicio/serializers.py
git add proyecto_django/servicio/views.py
git add proyecto_django/servicio/urls.py
git add proyecto_django/servicio/migrations/
git add proyecto_django/taller/settings.py
git add poblar_datos.py
git add pruebas_api.http
git add requirements.txt

git commit -m "tarea 07 - fix posts faltantes, fecha_ingreso, idempotencia"
git push
```