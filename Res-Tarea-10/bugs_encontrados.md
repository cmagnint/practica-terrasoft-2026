# Bugs Encontrados — Tarea 10

## Sintoma 1 — Cálculo incorrecto de costo_total

**Archivo:** `proyecto_django/servicio/models.py`
**Función/Método:** `RepuestoOrden.save()`

**Codigo roto:**

```python
self.costo_total = self.costo_unitario + self.cantidad
```

**Codigo corregido:**

```python
self.costo_total = self.costo_unitario * self.cantidad
```

**Explicacion:**

El costo total del repuesto debia calcularse multiplicando, costo unitario por la cantidad utilizada, el codigo actual realizaba una suma,
generando el resultado incorrecto, por ejemplo para un costo unitario de 8500 y cantidad 2, el sistema devolvia 8502 en lugar de 17000,
ahi se observa que estaba sumando en vez de multiplicar


**Como lo reproduje:**

```POST http://127.0.0.1:8000/api/repuestos/
Authorization: Bearer {{loginAdmin.response.body.access}}
Content-Type: application/json

{
    "orden": 26,
    "proveedor": "AutoParts SpA",
    "detalle": "Filtro de aceite",
    "costo_unitario": 8500,
    "cantidad": 2,
    "archivo_origen": "prueba_manual.xlsx",
    "fila_excel": 9
}```
El campo `costo_total` devolvía `8502.00`.

## Sintoma 2 — Permiso incorrecto para crear órdenes

**Archivo:** `proyecto_django/servicio/permissions.py`
**Función/Metodo:** `EsAdministradorOMecanico.has_permission()`

**Codigo roto:**

```python
return (
    es_admin(request.user)
    and
    es_mecanico(request.user)
)
```

**Codigo corregido:**

```python
return (
    es_admin(request.user)
    or
    es_mecanico(request.user)
)
```

**Explicación:**

El permiso debia permitir acceso a administradores o mecanicos. El uso de `and` obligaba a que el usuario perteneciera simultaneamente a ambos roles,
condician que ningun usuario cumplia. Como resultado, el endpoint devolviia 403

**Como lo reproduje:**

```POST http://127.0.0.1:8000/api/ordenes/
Authorization: Bearer {{loginAdmin.response.body.access}}
Content-Type: application/json

{
    "vehiculo": 1,
    "mecanico": 2,
    "descripcion": "Revision general",
    "fecha_entrega_estimada": "2026-07-01"
}```

Usando `admin_taller` o `carlos_munoz`, ambos recibían `403 Forbidden`


## Bug 3 — Mecánico bloqueado en sus propias órdenes

**Archivo:** `proyecto_django/servicio/views.py`
**Función/Método:** `OrdenViewSet.get_object()`

**Codigo roto:**

```python
orden.mecanico.usuario == user
```

**Codigo corregido:**

```python
orden.mecanico.usuario != user
```

**Explicación:**

La validación estaba invertida, el sistema lanzaba una excepcion cuando la orden pertenecia al mecanico autenticado,
bloqueando sus propias ordenes y permitiendo operar sobre ordenes ajenas

**Como lo reproduje:**

```POST http://127.0.0.1:8000/api/ordenes/1/completar/
Authorization: Bearer {{loginMecanico.response.body.access}}
Content-Type: application/json

{
    "monto": 45000,
    "fecha_entrega_real": "2026-06-10"
}```
Como mecanico, al intentar completar una orden propia obtenía `403 Forbidden`


## Bug 4 — Lista de mecanicos disponibles invertida

**Archivo:** `proyecto_django/servicio/views.py`
**Función/Método:** `MecanicoViewSet.disponibles()`

**Codigo roto:**

```python
ordenes_activas_count__gte=3
```

**Código corregido:**

```python
ordenes_activas_count__lt=3
```

**Explicación:**

El endpoint debía mostrar mecánicos con menos de tres órdenes activas, el filtro original seleccionaba exactamente a los mas ocupados,
ya que gte significa Greater Than or Equal, mayor o igual que, por eso nostraba a aquellos con tres o mas ordenes activas

**Cómo lo reproduje:**

```http
GET /api/mecanicos/disponibles/
```

La respuesta mostraba mecanicos con alta carga de trabajo en lugar de los disponibles


## Bug 5 — Auditoría con datos invertidos

**Archivo:** `proyecto_django/servicio/views.py`
**Función/Método:** `OrdenViewSet.completar()`

**Codigo roto:**

```python
datos_previos={
    'estado': orden.estado,
    ...
},
datos_nuevos=datos_previos,
```

**Codigo corregido:**

```python
datos_previos=datos_previos,

datos_nuevos={
    'estado': orden.estado,
    ...
},
```

**Explicacion:**

Los datos almacenados en la auditoría estaban invertidos, el estado posterior al cambio se guardaba como dato previo y viceversa,
la operacion funcionaba correctamente, pero el registro historico quedaba inconsistente

**Como lo reproduje:**

```http
POST /api/ordenes/<id>/completar/
GET /api/audit-logs/?accion=completar_orden
```

El log mostraba `"Completada"` en `datos_previos` y `"Pendiente"` en `datos_nuevos`


## Bug 6 — Errores de importacion no acumulados

**Archivo:** `scripts/importar_repuestos.py`
**Función/Método:** `main()`

**Codigo roto:**

```python
todos_errores = resultado['errores']
```

**Codigo corregido:**

```python
todos_errores.extend(
    resultado['errores']
)
```

**Explicacion:**

Cada iteracion reemplazaba la lista completa de errores por los errores del archivo mas reciente, 
como consecuencia, el resumen final mostraba unicamente los errores del ultimo Excel procesado

**Como lo reproduje:**

```bash
python scripts/importar_repuestos.py
```

El resultado final indicaba solamente los errores del ultimo archivo procesado


## Bug 7 — Orden de rentabilidad invertido

**Archivo:** `scripts/generar_informe.py`
**Función/Método:** Generación de resumen de rentabilidad

**Código roto:**

```python
resumen = resumen.sort_values(
    by='margen_pct',
    ascending=True
)
```

**Código corregido:**

```python
resumen = resumen.sort_values(
    by='margen_pct',
    ascending=False
)
```

**Explicacion:**

La especificación indicaba que el informe debía mostrar primero a los mecánicos con mayor rentabilidad, 
el orden ascendente colocaba primero a los menos rentables.

**Como lo reproduje:**

```bash
python scripts/generar_informe.py
```

Al revisar `informe_rentabilidad.xlsx`, la hoja **Resumen por Mecanico** mostraba inicialmente los márgenes mas bajos al comienzo del listado
