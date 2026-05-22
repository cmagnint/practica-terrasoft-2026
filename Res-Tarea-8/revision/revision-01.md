# 📋 Re-trabajo Tarea 8 — Errores detectados

---

## 🔴 BLOQUEANTES

### 1. `poblar_datos.py` no ejecuta

**Archivo:** `poblar_datos.py:4`

**Evidencia:**
```
$ python poblar_datos.py
ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured
```

**Spec violada (8.2.3 y 8.3.4):** debe crear los usuarios `admin_taller`, `carlos_munoz`, `juan_perez`, los grupos `admin`/`mecanico`/`cliente`, y vincular `carlos_munoz` con un `Mecanico` y `juan_perez` con un `Cliente`.

**Observación adicional:** existe un management command duplicado en `servicio/management/commands/poblar_datos.py` que crea usuarios distintos (`mecanico1`, `cliente1`). Dos scripts desincronizados, ninguno cumple la spec.

---

### 2. Rutas JWT incorrectas

**Archivo:** `taller/urls.py:39`

**Evidencia:**
```
POST /api/auth/login/  → 404
POST /api/auth/refresh/ → 404
```

Las rutas existen bajo `/api/token/` en lugar de `/api/auth/...`.

**Spec violada (8.2.2):** los endpoints son `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/verify/`.

---

### 3. `MecanicoViewSet.retrieve()` devuelve 500

**Archivo:** `servicio/views.py:78`

**Evidencia:**
```
GET /api/mecanicos/11111111-1/ → 500
AssertionError: Expected a Response, HttpResponse or HttpStreamingResponse to be returned, but received a `<class 'NoneType'>`
```

**Spec violada (8.1.1):** `retrieve()` debe devolver detalle con `ordenes_activas` y `stats`.

**Pista:** mira la indentación del bloque que arma la respuesta del detalle. No está donde debería.

---

### 4. `POST /api/ordenes/` revienta con IntegrityError

**Archivo:** `servicio/models.py:134` + `servicio/serializers.py:143`

**Evidencia:**
```
POST /api/ordenes/ como admin → 500
IntegrityError: null value in column "fecha_ingreso" violates not-null constraint
```

**Spec violada:** acción auditable `crear_orden` requiere que `POST /api/ordenes/` retorne 201.

**Pista:** revisa qué tenía `fecha_ingreso` en Tarea 7 y compáralo con tu migración actual.

---

### 5. `POST /api/vehiculos/` revienta con IntegrityError

**Archivo:** `servicio/views.py:357`

**Evidencia:**
```
POST /api/vehiculos/ {"patente":"ZZ9900",...,"cliente":1} como admin → 500
IntegrityError: null value in column "cliente_id"
```

**Pista:** existe `VehiculoCreateSerializer` en el código, pero ningún ViewSet lo usa. ¿Por qué se ignora?

---

### 6. Permisos por rol no funcionan

**Archivos:** `servicio/permissions.py:4`, `servicio/views.py:201`, `servicio/views.py:352`, `servicio/views.py:542`

**Evidencia (matriz real vs esperada):**

| Acción | Obtenido | Esperado |
|--------|----------|----------|
| `POST /api/clientes/` como mecánico | **201** | 403 |
| `POST /api/clientes/` como cliente | **201** | 403 |
| `GET /api/vehiculos/` como Juan (cliente) | 36 vehículos | 3 (los suyos) |
| `GET /api/ordenes/` como Juan (cliente) | **403** | sus órdenes |
| `GET /api/clientes/` como Carlos (mecánico) | 24 clientes | 8 (con `.distinct()`) |
| Usuario en grupo `admin` sin `is_staff` accediendo a `/api/audit-logs/` | **403** | 200 |

**Spec violada (8.3.5 y 8.3.6):** los helpers `es_admin`/`es_mecanico`/`es_cliente` deben mirar `user.groups`, no `is_staff` ni la relación OneToOne. Cada ViewSet debe tener `get_permissions()` y `get_queryset()` específicos por rol.

**Pista:** hoy `EsAdministrador` solo revisa `is_staff`. Esa es la raíz de varios bugs encadenados.

---

### 7. Mecánico modificando orden ajena devuelve 404, no 403

**Archivo:** `servicio/views.py:573`

**Evidencia:**
```
POST /api/ordenes/62/completar/ como Carlos (orden no asignada a él)
→ 404 {"detail":"No OrdenTrabajo matches the given query."}
```

**Spec violada (8.3.6):** debe lanzar `PermissionDenied('Solo puedes modificar tus propias órdenes')` → 403.

**Pista:** la orden existe en BD, pero tu filtrado por queryset la oculta antes de chequear permisos. El comportamiento correcto es encontrarla y entonces denegar.

---

### 8. Auditoría incompleta

**Archivos:** `servicio/views.py:147`, `servicio/views.py:700`, `servicio/views.py:926`

**Evidencia tras ejecutar cada acción exitosamente:**

| Acción | Se registró | `datos_previos` | `datos_nuevos` |
|--------|-------------|-----------------|----------------|
| `crear_cliente` | **NO** | — | — |
| `actualizar_cliente` | **NO** | — | — |
| `crear_vehiculo` | — (acción falla) | — | — |
| `crear_orden` | — (acción falla) | — | — |
| `completar_orden` | Sí | **null** | OK |
| `cancelar_orden` | Sí | OK | OK |
| `desactivar_mecanico` | **NO** | — | — |

**Spec violada (8.3.2):** las 7 acciones listadas deben auditarse.

**Pista:** `completar_orden` registra pero `datos_previos` queda null. ¿Cuándo estás capturando el estado previo?

---

### 9. Filtros de `/api/audit-logs/` no funcionan

**Archivo:** `servicio/views.py` — `AuditLogViewSet`

**Evidencia:**
```
GET /api/audit-logs/?accion=crear_cliente
→ 200 con acciones ['completar_orden','cancelar_orden','completar_orden']
```

**Spec violada (8.3.8):** debe filtrar por `usuario`, `accion`, `modelo`, `desde`, `hasta`.

**Pista:** `AuditLogViewSet` no tiene `get_queryset()` override.

---

## 🟡 IMPORTANTES

### 10. `MecanicoViewSet` permite DELETE

**Archivo:** `servicio/views.py:45`

**Evidencia:**
```
DELETE /api/mecanicos/99000000-9/ como admin → 204
```

**Spec violada (8.1.1):** "No implementes `destroy()` — los mecánicos no se borran, se desactivan con `@action`".

---

### 11. `disponibles/` requiere admin

**Archivo:** `servicio/views.py:49`

**Evidencia:**
```
GET /api/mecanicos/disponibles/ como Carlos (mecánico) → 403
```

**Spec violada (8.3.6):** "Excepción: `disponibles/` que cualquier autenticado puede ver".

---

### 12. Filtro `?buscar=` rompe con 500

**Archivo:** `servicio/views.py:225`

**Evidencia:**
```
GET /api/clientes/?buscar=Juan → 500
FieldError: Cannot resolve keyword 'nombre_icontains' into field
```

**Pista:** cuenta los underscores.

---

### 13. Paginación estándar no aplicada

**Archivos:** `servicio/views.py:661`, `taller/settings.py:148`, `servicio/pagination.py` (no existe)

**Evidencia:**
```
GET /api/ordenes/ → {"total": 60, "ordenes": [...]}
GET /api/ordenes/?page=2&page_size=10 → devuelve los 64, ignora paginación
```

**Spec violada (8.4.2):** debe devolver `{count, next, previous, results}` con `PAGE_SIZE=20`, archivo `servicio/pagination.py` con `StandardPagination`.

**Pista:** tus `list()` custom serializan a mano y nunca llaman a la paginación de DRF.

---

### 14. JWT con duración incorrecta

**Archivo:** `taller/settings.py:162`

**Evidencia:** `ACCESS_TOKEN_LIFETIME_seconds = 3600` (60 min).

**Spec violada (8.2.1):** `timedelta(minutes=30)`.

---

### 15. README desalineado con la spec

**Archivo:** `README.md:80,105,131`

**Evidencias:**
- Credenciales documentadas: `admin/mecanico1/cliente1` → spec exige `admin_taller/carlos_munoz/juan_perez`.
- Curl de login: `/api/token/` → spec exige `/api/auth/login/`.
- Tabla de endpoints: dice que cliente NO puede ver `GET /api/ordenes/` → spec exige que SÍ vea las suyas.

---

## 🟢 MENORES

### 16. Falta `servicio/pagination.py`
No existe el archivo que la spec lista en "Entrega final".

### 17. `extend_schema` faltante en acciones custom

**Evidencia:**
```
GET /api/schema/ → completar.requestBody referencia OrdenTrabajo completo
```

**Spec violada (8.4.3):** debe documentar `monto` y `fecha_entrega_real` como body de `completar`. Aplicar a los 5 endpoints custom más importantes.

`MeView` también genera warning de drf-spectacular por falta de serializer.

### 18. N+1 en `GET /api/mecanicos/`

**Evidencia:** 12 queries para listar 8 mecánicos, incluyendo 9 `COUNT(*)` separados (uno por fila).

**Causa:** `MecanicoSerializer.get_total_ordenes()` hace `obj.ordenes.count()` por fila.

**Spec violada:** Tarea 7 exigía optimización de queries; Tarea 8 asume que sobrevive al refactor.

---

## 📊 Resumen de impacto por sub-tarea

| Sub-tarea | Errores bloqueantes | Estado |
|-----------|---------------------|--------|
| 8.1 ViewSets | #3, #10, #11 | ❌ |
| 8.2 JWT | #2, #14 | ❌ |
| 8.3 Permisos + Audit | #1, #4, #5, #6, #7, #8, #9 | ❌ |
| 8.4 CORS + paginación + docs | #13, #15 | ❌ |

---

## ✅ Cómo saber que terminaste

Cuando estos 15 pasos pasen en orden:

1. `python poblar_datos.py` corre limpio e idempotente, crea 3 usuarios + 3 grupos + vínculos.
2. `POST /api/auth/login/` con `admin_taller/admin123` → 200 con `{access, refresh}`.
3. `GET /api/auth/me/` con cada token → rol correcto.
4. `GET /api/mecanicos/<rut>/` → 200 con `ordenes_activas` y `stats`.
5. `GET /api/vehiculos/` como Juan → solo sus vehículos, cuenta coincide con SQL.
6. `GET /api/ordenes/` como Juan → 200 con sus órdenes.
7. `POST /api/clientes/` como Juan → 403.
8. `POST /api/clientes/` como Carlos → 403.
9. `POST /api/ordenes/` como admin → 201.
10. `POST /api/vehiculos/` como admin → 201.
11. `GET /api/audit-logs/?accion=crear_orden` tras paso 9 → contiene la entrada.
12. `POST /api/ordenes/<pk_ajena>/completar/` como Carlos → 403.
13. `DELETE /api/mecanicos/<rut>/` → 405.
14. `GET /api/ordenes/?page=2&page_size=10` → `{count, next, previous, results}` con 10 items.
15. `GET /api/docs/` carga Swagger sin warnings críticos.

---

## 📌 Notas

- **Cambios quirúrgicos.** Modifica lo mínimo para arreglar cada error. No reformatees código no relacionado.
- **Un solo camino.** No agregues fallbacks ni "por si acaso".
- **Tu filtrado de órdenes por mecánico funciona** (10 vs 10 en SQL). No lo toques, solo arregla los otros roles.
- **Migración 0003 está bien aplicada.** Los modelos están correctos. El problema está en views/serializers/permissions/poblado.