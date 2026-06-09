# Tarea 10 — Debugging: el proyecto que llegó roto

> **Esta tarea es diferente a todas las anteriores. No construyes nada nuevo.**
> Tu trabajo es encontrar los errores que dejó alguien más, entender por qué rompen el sistema y corregirlos.

---

## Contexto

El dueño del taller contrató a un desarrollador externo para hacer mejoras menores al sistema. Ese desarrollador entregó el código, pero **al pasar a producción, varias cosas dejaron de funcionar correctamente**.

Te llaman a ti para diagnosticar y corregir.

> *"Mira, no sé qué tocó este tipo. El sistema arranca, no explota, pero las cosas no están funcionando como antes. Los mecánicos se quejan de que no pueden completar órdenes. El informe de rentabilidad está ordenado al revés. Y el log de errores del script no cuadra. Necesito que lo revises todo y me digas qué estaba mal."*

El proyecto está en `Res-Tarea-10/`. Es una copia del sistema de Tarea 9 con **7 bugs introducidos**.

---

## Setup inicial (igual que Tarea 9)

```bash
cd Res-Tarea-10/proyecto_django
python manage.py migrate
python manage.py runserver

# En otra terminal:
cd Res-Tarea-10/proyecto_django
python poblar_datos.py   # ← está un nivel arriba, ajusta la ruta
```

> Usa una base de datos limpia. El archivo `.env.example` tiene la configuración.
> Verifica que exista `admin_taller` y que haya órdenes en estado `Completada`.

---

## Los 7 síntomas

Estos son los síntomas reportados. **No te dicen en qué archivo está el bug** — eso lo tienes que descubrir tú.

---

### Síntoma 1 — `costo_total` incorrecto al crear un repuesto

Al hacer:

```http
POST /api/repuestos/
Content-Type: application/json
Authorization: Bearer <token_admin>

{
    "orden": <id_orden_completada>,
    "proveedor": "AutoParts SpA",
    "detalle": "Filtro de aceite",
    "costo_unitario": 8500,
    "cantidad": 2,
    "archivo_origen": "prueba_manual.xlsx",
    "fila_excel": 1
}
```

La respuesta incluye un `costo_total` que **no es `17000.00`**.

---

### Síntoma 2 — Admin y mecánico no pueden crear órdenes de trabajo

```http
POST /api/ordenes/
Authorization: Bearer <token_admin>
Content-Type: application/json

{
    "vehiculo": 1,
    "mecanico": 1,
    "descripcion": "Revisión general",
    "fecha_entrega_estimada": "2026-07-01"
}
```

Tanto `admin_taller` como `carlos_munoz` (mecánico) reciben `403 Forbidden`.

El endpoint `GET /api/ordenes/` funciona correctamente para ambos.

---

### Síntoma 3 — El mecánico recibe 403 al completar sus propias órdenes

Logueado como mecánico (`carlos_munoz`):

```http
POST /api/ordenes/<id_orden_de_carlos>/completar/
Authorization: Bearer <token_mecanico>
Content-Type: application/json

{"monto": 45000, "fecha_entrega_real": "2026-06-10"}
```

Devuelve `403 Forbidden`. Sin embargo, el mismo mecánico **puede** completar órdenes asignadas a otros mecánicos.

> Nota: este síntoma solo se puede reproducir después de corregir el Síntoma 2, porque hasta entonces el permiso de nivel superior bloquea antes de llegar al objeto.

---

### Síntoma 4 — `GET /api/mecanicos/disponibles/` devuelve la lista incorrecta

El endpoint debería devolver mecánicos activos con **menos de 3 órdenes activas** (disponibles para tomar nuevas órdenes). Pero devuelve los mecánicos que tienen **3 o más** órdenes activas — exactamente los que están más ocupados.

Pista: compara el resultado de `/api/mecanicos/disponibles/` con el resultado de `/api/mecanicos/?activo=true` y revisa cuántas órdenes activas tiene cada uno.

---

### Síntoma 5 — El AuditLog de `completar_orden` muestra datos al revés

Después de completar una orden:

```http
GET /api/audit-logs/?accion=completar_orden
Authorization: Bearer <token_admin>
```

El campo `datos_previos` muestra el estado **después** del cambio (por ejemplo `"estado": "Completada"`), y `datos_nuevos` muestra el estado **antes** (`"estado": "Pendiente"`). Están invertidos.

La orden se completa correctamente — el bug no afecta la operación, solo el registro de auditoría.

---

### Síntoma 6 — El script de importación reporta menos errores de los reales

Al ejecutar `importar_repuestos.py` con los 3 Excel de Tarea 9:

```
Procesando archivo: repuestos_proveedor_lote_1.xlsx
Errores: 90

Procesando archivo: repuestos_proveedor_lote_2.xlsx
Errores: 90

Procesando archivo: repuestos_proveedor_lote_3.xlsx
Errores: 90

========================================
RESULTADO GENERAL
Errores: 90          ← debería ser 270
========================================
```

El resumen final muestra solo los errores del **último archivo**, no la suma de los tres. El Excel `errores_importacion.xlsx` también tiene solo 90 filas en vez de 270.

---

### Síntoma 7 — El informe de rentabilidad ordena los mecánicos al revés

Al generar `informe_rentabilidad.xlsx`, la hoja `Resumen por Mecánico` muestra los mecánicos ordenados de **menor a mayor margen porcentual** — el menos rentable aparece primero.

La especificación dice que deben aparecer de **mayor a menor** (el más rentable primero).

---

## Entrega

```
Res-Tarea-10/
├── proyecto_django/
│   └── servicio/
│       ├── models.py         ← corregido
│       ├── permissions.py    ← corregido
│       └── views.py          ← corregido
├── scripts/
│   ├── importar_repuestos.py ← corregido
│   └── generar_informe.py    ← corregido
└── bugs_encontrados.md       ← NUEVO
```

---

## Formato de `bugs_encontrados.md`

Para cada uno de los 7 bugs, documenta:

```markdown
## Bug N — Nombre descriptivo del bug

**Archivo:** `ruta/al/archivo.py`
**Función/Método:** nombre de la función donde está

**Código roto:**
```python
# línea exacta con el error
```

**Código corregido:**

```python
# línea corregida
```

**Explicación:**
Por qué este código produce el síntoma observado. Qué concepto de Django/Python
viola. Cómo lo descubriste.

**Cómo lo reproduje:**
El request o comando exacto que evidenció el bug.

```

---

## Checklist de verificación

- [ ] `POST /api/repuestos/` con `costo_unitario=8500` y `cantidad=2` devuelve `"costo_total": "17000.00"`.
- [ ] `POST /api/ordenes/` como `admin_taller` devuelve `201 Created`.
- [ ] `POST /api/ordenes/` como mecánico devuelve `201 Created`.
- [ ] Mecánico hace `POST /api/ordenes/<id_propio>/completar/` y recibe `200 OK`.
- [ ] Mecánico hace `POST /api/ordenes/<id_otro_mecanico>/completar/` y recibe `403`.
- [ ] `GET /api/mecanicos/disponibles/` devuelve solo mecánicos con **menos de 3** órdenes activas.
- [ ] `GET /api/audit-logs/?accion=completar_orden` muestra `datos_previos.estado` como el estado **anterior** a completar (ej. `"Pendiente"`).
- [ ] `importar_repuestos.py` con los 3 Excel reporta `Errores: 270` en el resumen general.
- [ ] `errores_importacion.xlsx` tiene 270 filas.
- [ ] `informe_rentabilidad.xlsx` hoja `Resumen por Mecánico` muestra el mecánico con **mayor margen primero**.
- [ ] `bugs_encontrados.md` documenta los 7 bugs con código roto, código corregido y explicación.

---

## Commits esperados

```bash
# Un commit por bug corregido
git add proyecto_django/servicio/models.py
git commit -m "tarea 10 - bug 1: corregir calculo de costo_total"

git add proyecto_django/servicio/permissions.py
git commit -m "tarea 10 - bug 2: corregir EsAdministradorOMecanico"

git add proyecto_django/servicio/views.py
git commit -m "tarea 10 - bugs 3/4/5: corregir get_object, disponibles y audit"

git add scripts/importar_repuestos.py
git commit -m "tarea 10 - bug 6: corregir acumulacion de errores"

git add scripts/generar_informe.py
git commit -m "tarea 10 - bug 7: corregir orden del resumen"

git add bugs_encontrados.md
git commit -m "tarea 10 - documentacion de bugs encontrados"
```

> Puedes agrupar los commits como prefieras, pero cada bug debe mencionarse en algún commit.

---
