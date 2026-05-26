    # 📋 Tarea 8 — Hallazgos pendientes tras re-revisión

---

## ✅ Lo que ya está bien (no toques)
- #1 `poblar_datos.py` — funciona, crea usuarios, grupos y vínculos.
- #2 Rutas JWT — `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/verify/` responden.

---

## #3 — `MecanicoViewSet.retrieve()` clave incorrecta ⚠️ PARCIAL

**Archivo:** `servicio/views.py`

**Evidencia:** `GET /api/mecanicos/11111111-1/` devuelve clave `"ordenes activas"` (con espacio).

**Spec violada:** la clave debe ser `"ordenes_activas"` (con underscore).

---

## #4 — `POST /api/ordenes/` sigue roto ❌

**Archivo:** `servicio/models.py` + migración

**Evidencia:**
```
POST /api/ordenes/ como admin → 500
IntegrityError: null value in column "fecha_ingreso" violates not-null constraint
```

**Pista:** Tarea 7 tenía `fecha_ingreso` con `auto_now_add=True`. Compara tu `models.py` actual con la spec de Tarea 7 y revisa qué hace tu migración `0002_alter_ordentrabajo_fecha_ingreso.py`.

---

## #5 — `POST /api/vehiculos/` sigue roto ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
POST /api/vehiculos/ como admin → 500
IntegrityError: null value in column "cliente_id"
```

**Pista:** Ya existe `VehiculoCreateSerializer` en tu código. El problema está en que `VehiculoViewSet` nunca lo usa. Busca cómo `OrdenViewSet` resuelve el mismo problema y aplica el mismo patrón.

---

## #6 — Permisos por rol mal aplicados ⚠️ PARCIAL

**Archivos:** `servicio/permissions.py`, `servicio/views.py`

**Evidencia (status codes reales obtenidos):**

| Acción | admin | mecánico | cliente | Esperado |
|--------|-------|----------|---------|----------|
| `POST /api/clientes/` | 201 | 403 | 403 | 201/403/403 ✅ |
| `GET /api/clientes/` como Carlos | — | 403 | — | 200 (sus 8 clientes) ❌ |
| `GET /api/ordenes/` como Juan | — | — | 403 | 200 (sus 4 órdenes) ❌ |
| `GET /api/vehiculos/` como Juan | — | — | 200 (35) | 200 (sus 3) ❌ |
| `GET /api/vehiculos/` como Carlos | — | 200 (35) | — | 200 (sus N) ❌ |
| `GET /api/mecanicos/disponibles/` como Carlos | — | 403 | — | 200 ❌ |
| Usuario en grupo `admin` sin `is_staff` → `/api/audit-logs/` | 403 | — | — | 200 ❌ |

**Causa raíz:** `permissions.py` define `EsAdministrador` mirando `is_staff`, no el grupo `admin`. `EsMecanico`/`EsCliente` miran la relación OneToOne, no los grupos. Los `get_queryset()` de `ClienteViewSet`, `VehiculoViewSet` y `OrdenViewSet` no diferencian los 3 roles. Revisa la spec sección 8.3.5 y 8.3.6 completa.

---

## #7 — Mecánico completando orden ajena devuelve 404 en vez de 403 ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
POST /api/ordenes/62/completar/ como Carlos (orden no es suya) → 404
```
**Esperado:** 403 con mensaje `"Solo puedes modificar tus propias órdenes"`.

**Pista:** La orden existe en BD. El problema es que tu `get_queryset()` la filtra antes de que llegue a `get_object()`, así DRF reporta 404 en vez de 403. Busca en la spec 8.3.6 cómo se indica resolver este caso y dónde debe ir esa validación.

---

## #8 — Auditoría incompleta ⚠️ PARCIAL

**Archivo:** `servicio/views.py`, `servicio/audit.py`

**Evidencia:**

| Acción | Se registró | `datos_previos` | `datos_nuevos` |
|--------|-------------|-----------------|----------------|
| `crear_cliente` | ❌ No | — | — |
| `actualizar_cliente` | ❌ No | — | — |
| `crear_vehiculo` | — (acción falla 500) | — | — |
| `crear_orden` | — (acción falla 500) | — | — |
| `completar_orden` | ✅ Sí | ❌ null | ✅ OK |
| `cancelar_orden` | ✅ Sí | ✅ OK | ✅ OK |
| `desactivar_mecanico` | ❌ No | — | — |

**Pista 1:** `registrar_audit()` solo se llama en `completar` y `cancelar`. Las demás acciones exitosas no lo llaman. Revisa cada acción auditable de la spec y asegúrate de llamarlo después del `save()` exitoso.

**Pista 2:** En `completar_orden`, `datos_previos = null`. ¿En qué momento del flujo estás capturando el estado anterior?

---

## #9 — Filtros del `AuditLogViewSet` no funcionan ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
GET /api/audit-logs/?accion=crear_cliente → 200
body: [{"accion":"cancelar_orden"}, {"accion":"completar_orden"}]
```

El parámetro `?accion=` se ignora completamente.

**Pista:** `AuditLogViewSet` no tiene `get_queryset()` override. Revisa la spec sección 8.3.8 — los 5 filtros requeridos están documentados ahí.

---

## #10 — `DELETE /api/mecanicos/` permitido ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
DELETE /api/mecanicos/99000000-9/ como admin → 204
```

**Spec violada (8.1.1):** "No implementes `destroy()` — los mecánicos no se borran, se desactivan con `@action`".

---

## #11 — `disponibles/` bloquea mecánicos y clientes ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
GET /api/mecanicos/disponibles/ como carlos_munoz → 403
GET /api/mecanicos/disponibles/ como juan_perez  → 403
```

**Spec violada (8.3.6):** "Excepción: `disponibles/` que cualquier autenticado puede ver."

Este se arregla solo cuando implementes correctamente `get_permissions()` en `MecanicoViewSet` — está relacionado con #6.

---

## #12 — Filtro `?buscar=` rompe con 500 ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
GET /api/clientes/?buscar=Juan → 500
FieldError: Cannot resolve keyword 'nombre_icontains' into field
```

**Pista:** Cuenta los underscores en ese lookup.

---

## #13 + #16 — Paginación estándar no aplicada + `pagination.py` no existe ❌

**Archivos:** `servicio/views.py`, `taller/settings.py`, `servicio/pagination.py` (no existe)

**Evidencia:**
```
GET /api/ordenes/ → {"total": 63, "ordenes": [...]}   ← estructura incorrecta
GET /api/ordenes/?page=2&page_size=10 → devuelve los 63 completos
```

**Spec violada (8.4.2):**
- Debe existir `servicio/pagination.py` con la clase `StandardPagination`.
- `GET /api/ordenes/` debe devolver `{count, next, previous, results}`.
- `PAGE_SIZE` en settings debe ser `20`.

**Pista:** Tus `list()` custom en los ViewSets serializan a mano y nunca llaman a la paginación de DRF. Los filtros (`?estado=`, `?marca=`, etc.) van en `get_queryset()`, no en `list()`. Los `@action` que devuelven listas (`resumen`, `disponibles`, `historial`) NO deben paginarse.

---

## #14 — JWT lifetime incorrecto ❌

**Archivo:** `taller/settings.py`

**Evidencia:** `ACCESS_TOKEN_LIFETIME` son 3600 segundos (60 min).

**Spec violada (8.2.1):** debe ser `timedelta(minutes=30)`.

---

## #15 — README desalineado ❌

**Archivo:** `README.md`

**Evidencia:**
- Documenta credenciales `admin/mecanico1/cliente1` → deben ser `admin_taller/carlos_munoz/juan_perez`.
- Documenta login en `/api/token/` → debe ser `/api/auth/login/`.
- Tabla de roles dice que cliente NO puede ver `GET /api/ordenes/` → debe poder ver las suyas.

---

## #17 — `extend_schema` faltante ❌

**Archivo:** `servicio/views.py`

**Evidencia:**
```
GET /api/schema/ → completar.requestBody = "#/components/schemas/OrdenTrabajo"
```

**Spec violada (8.4.3):** el body de `completar` debe documentar `monto` y `fecha_entrega_real`. Aplicar `@extend_schema` a los 5 endpoints custom más importantes. `MeView` también genera warning por falta de serializer.

---

## #18 — N+1 en `GET /api/mecanicos/` ❌

**Archivo:** `servicio/views.py`, `servicio/serializers.py`

**Evidencia:** 15 queries para listar 8 mecánicos, incluye 13 `COUNT(*)` individuales.

**Pista:** `MecanicoSerializer.get_total_ordenes()` hace `obj.ordenes.count()` por cada fila. La solución está en `get_queryset()` del ViewSet con una anotación, y en el serializer leer esa anotación en vez de hacer el count.

---

## 🆕 Regresiones nuevas

### R1 — CORS devuelve `Access-Control-Allow-Origin: null`

**Evidencia:**
```
OPTIONS /api/mecanicos/ -H "Origin: http://localhost:3000"
→ Access-Control-Allow-Origin: null
```

**Spec violada (8.4.1):** debe devolver `Access-Control-Allow-Origin: http://localhost:3000`.

**Pista:** Verifica que `corsheaders` esté en `INSTALLED_APPS`, que `CorsMiddleware` sea el **primer** middleware de la lista, y que `CORS_ALLOWED_ORIGINS` tenga la URL correcta.

---

### R2 — `/api/redoc/` devuelve 404

**Evidencia:**
```
GET /api/redoc/ → 404
```

**Spec violada (8.4.3):** debe existir junto a `/api/docs/` y `/api/schema/`.

**Pista:** Revisa `taller/urls.py` — probablemente falta registrar la ruta `SpectacularRedocView`.

---

### R3 — `admin_taller` no es superuser

**Evidencia:** `User.objects.get(username='admin_taller').is_superuser → False`

**Spec violada (8.2.3):** el snippet de la spec crea `admin_taller` con `is_superuser=True`. Esto explica por qué en #6 el superuser sin grupo `admin` no pasa el permiso — porque además no es superuser.

**Pista:** Revisa `poblar_datos.py` en el bloque de `admin_taller`. Si el usuario ya existe y fue creado sin `is_superuser`, `get_or_create` no lo actualiza.

---

## ✅ Checklist de validación final

Ejecuta todo en orden. Si pasa los 19, entrega.

1. `python poblar_datos.py` corre dos veces sin error.
2. `User.objects.get(username='admin_taller').is_superuser` → `True`.
3. `POST /api/auth/login/ {"username":"admin_taller","password":"admin123"}` → 200.
4. `GET /api/auth/me/` con cada token → rol correcto para los 3 usuarios.
5. `GET /api/mecanicos/<rut>/` → 200 con clave **`ordenes_activas`** (underscore).
6. `POST /api/ordenes/ {...}` como admin → 201.
7. `POST /api/vehiculos/ {...}` como admin → 201.
8. `GET /api/vehiculos/` como Juan → solo sus vehículos (no los 35).
9. `GET /api/ordenes/` como Juan → 200 con sus órdenes (no 403).
10. `GET /api/clientes/` como Carlos → 200 con sus clientes (no 403).
11. `GET /api/mecanicos/disponibles/` como Carlos → 200.
12. `POST /api/ordenes/<pk_ajena>/completar/` como Carlos → **403** (no 404).
13. `DELETE /api/mecanicos/<rut>/` → **405**.
14. `GET /api/clientes/?buscar=Juan` → 200 (no 500).
15. `GET /api/ordenes/` → response tiene claves `count`, `next`, `previous`, `results`.
16. `GET /api/ordenes/?page=2&page_size=10` → 10 items en `results`.
17. Tras `POST /api/clientes/`, `GET /api/audit-logs/?accion=crear_cliente` → contiene la entrada.
18. `OPTIONS /api/mecanicos/ -H "Origin: http://localhost:3000"` → header `Access-Control-Allow-Origin: http://localhost:3000`.
19. `GET /api/redoc/` → 200.