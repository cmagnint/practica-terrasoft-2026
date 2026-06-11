# Tarea 11 — Proyecto nuevo desde cero: backend a frontend

## Contexto: Huerto Santa Elena

Cambias de rubro. Vuelves al campo, pero con un sistema serio y full-stack.

> *"Administro un huerto de arándanos grande. Tengo supervisores a cargo de cuadrillas de
> cosecheros, y cada cosechero registra cuántos kilos saca por cuartel y por día. Hoy lo
> llevo en cuadernos. Quiero un sistema donde cada supervisor vea solo a su gente y sus
> cuarteles, cada cosechero vea solo lo suyo, y yo como administradora vea todo y saque
> métricas de rendimiento. La semana que viene quiero empezar a verlo en una pantalla web,
> así que dejá la base lista para conectarla."*

Tres actores, tres niveles de visibilidad:

| Rol                              | Qué ve / qué puede hacer                                                                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **admin** (la dueña)      | Todo. CRUD completo. Métricas globales. Auditoría.                                                                                                                |
| **supervisor**             | Solo**sus** cosecheros, **sus** cuarteles y los registros de **su** cuadrilla. Crea/edita registros de su gente. No ve datos de otras cuadrillas. |
| **trabajador** (cosechero) | Solo**sus propios** registros y su perfil. Lectura.                                                                                                           |

---

## Estructura del repositorio

Proyecto **monorepo** nuevo. Sin Docker. Backend y frontend separados:

```
Res-Tarea-11/
├── backend/
│   ├── proyecto_django/
│   │   ├── manage.py
│   │   ├── campo/              ← proyecto Django (settings, urls)
│   │   └── cosecha/            ← app principal
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       ├── permissions.py
│   │       ├── pagination.py
│   │       ├── audit.py
│   │       ├── tests.py
│   │       └── management/commands/poblar_datos.py
│   ├── pruebas_api.http
│   ├── .env.example           ← plantilla SIN secretos reales
│   └── requirements.txt
├── frontend/
│   └── campo-web/             ← Next.js (create-next-app)
│       ├── lib/api.ts
│       ├── app/page.tsx
│       └── .env.local.example
└── README.md
```

### Reglas de oro del proyecto (no negociables)

1. **Sin Docker.** PostgreSQL local o el que uses; la conexión se configura por `.env`.
2. **Cero secretos en el código.** `SECRET_KEY`, credenciales de BD, `DEBUG`, hosts → todo
   con `python-decouple`. Subes `.env.example` (plantilla), **nunca** `.env`. Agrega `.env`
   y `.env.local` al `.gitignore`.
3. **Todo error es JSON.** Nunca HTML de Django, nunca texto plano.
4. **Logger por método** (`logging.getLogger('cosecha')`) en cada acción que muta datos.
5. **`select_related` / `prefetch_related`** donde haya relaciones. Una N+1 en este proyecto
   cuenta como bug.

---

# Tarea 11.1 — Modela el dominio (tú diseñas)

**`cosecha/models.py`**

No se te entrega el modelo escrito. Se te entrega el **dominio**; tú decides tipos,
`related_name`, `on_delete`, índices, `Meta`, `__str__` y constraints.

### Entidades mínimas

**`Supervisor`**

- nombre, `rut` (único), zona (texto), `activo` (default True)
- `usuario` → `OneToOneField(User)`, nullable, `on_delete=SET_NULL`, `related_name='supervisor'`

**`Trabajador`** (el cosechero)

- nombre, `rut` (único), `fecha_ingreso`, `activo`
- `supervisor` → FK a `Supervisor`, `related_name='trabajadores'`. Un trabajador pertenece a
  una cuadrilla (un supervisor). `on_delete=PROTECT`.
- `usuario` → `OneToOneField(User)`, nullable, `related_name='trabajador'`

**`Cuartel`**

- `nombre` (único), `hectareas` (Decimal), variedad (choices: Duke / Legacy / Brigitta /
  Liberty), `activo`
- `supervisor` → FK a `Supervisor` (quién lo tiene a cargo), `related_name='cuarteles'`,
  `on_delete=PROTECT`

**`RegistroCosecha`** (el corazón del sistema)

- `trabajador` → FK, `related_name='registros'`, `on_delete=PROTECT`
- `cuartel` → FK, `related_name='registros'`, `on_delete=PROTECT`
- `fecha` (Date)
- `kilos` (Decimal, ≥ 0), `horas` (Decimal, 0 < horas ≤ 12)
- `calidad` (choices: Exportación / Nacional / Descarte)
- `observaciones` (blank)
- `creado_en` (auto_now_add)

**Reglas de integridad que debes imponer en el modelo (no solo en el serializer):**

- Un trabajador no puede tener **dos registros del mismo cuartel el mismo día** →
  `UniqueConstraint(fields=['trabajador', 'cuartel', 'fecha'])`.
- `Meta.ordering` razonable (registros por `-fecha`).
- Un trabajador y el cuartel donde registra **deben pertenecer al mismo supervisor**. Esta
  regla **no** se puede expresar con un constraint de BD simple — déjala documentada y
  válidala en el serializer (Tarea 11.2). Apúntala con un comentario en el modelo.

**`AuditLog`** — mismo espíritu que ya conoces (usuario, accion, modelo, objeto_id,
descripcion, datos_previos JSON, datos_nuevos JSON, timestamp). Diséñalo.

Crea migraciones y aplícalas. **No** uses `makemigrations` ciego: revisa el archivo de
migración generado y entiéndelo.

---

# Tarea 11.2 — Serializers (lectura ≠ escritura)

**`cosecha/serializers.py`**

Construye, como mínimo:

- `SupervisorSerializer` — incluye campo calculado `total_trabajadores` y `total_cuarteles`.
- `TrabajadorResumenSerializer` — `id`, `nombre`, `rut` (para anidar).
- `TrabajadorSerializer` — todos los campos + `supervisor` anidado (resumen) en lectura.
- `CuartelSerializer` — todos los campos + campo calculado `kilos_acumulados`
  (suma de `registros.kilos`, con `aggregate`, **no** en Python fila por fila).
- `RegistroCosechaSerializer` — lectura, con `trabajador` y `cuartel` anidados (resumen) y
  un campo calculado `rendimiento` = `kilos / horas` (redondea a 2 decimales).
- `RegistroCosechaCreateSerializer` — escritura, solo IDs. Implementa `validate()`:
  - `horas` en rango `(0, 12]`; `kilos ≥ 0`.
  - Si `calidad == 'Descarte'` y `kilos == 0` → error legible.
  - **Regla cruzada:** el `cuartel.supervisor` debe ser el mismo que el
    `trabajador.supervisor`. Si no, `ValidationError({'cuartel': 'El cuartel no pertenece a la cuadrilla del trabajador'})`.

> Los `DecimalField` se serializan como string por defecto. El frontend va a querer
> números. Decide y documenta cómo lo manejas (`coerce_to_string=False` o conversión
> explícita) y sé consistente en toda la API.

---

# Tarea 11.3 — Autenticación JWT + roles

Instala `djangorestframework-simplejwt`. Configura:

- `DEFAULT_AUTHENTICATION_CLASSES` → JWT.
- `DEFAULT_PERMISSION_CLASSES` → `IsAuthenticated` (todo cerrado por defecto, salvo lo que
  abras explícitamente).
- `ACCESS_TOKEN_LIFETIME` 30 min, `REFRESH_TOKEN_LIFETIME` 1 día.

Endpoints de auth en `campo/urls.py`:

| Endpoint                    | Qué hace                                                          |
| --------------------------- | ------------------------------------------------------------------ |
| `POST /api/auth/login/`   | `{username, password}` → `{access, refresh}`                  |
| `POST /api/auth/refresh/` | `{refresh}` → `{access}`                                      |
| `GET /api/auth/me/`       | Devuelve `{username, email, rol, perfil}` según quién consulta |

**`cosecha/permissions.py`** — helpers `es_admin(user)`, `es_supervisor(user)`,
`es_trabajador(user)` (basados en grupos `Group`) y las clases de permiso que necesites
(`EsAdmin`, `EsAdminOSupervisor`, `EsAdminOReadOnly`, …). **Usa los nombres que definas tú**
y sé consistente — nada de mezclar `IsAdmin` con `EsAdmin`.

`/api/auth/me/` debe resolver el `rol` por grupo y, si es supervisor o trabajador, anidar su
perfil correspondiente (`SupervisorSerializer` / `TrabajadorSerializer`).

---

# Tarea 11.4 — ViewSets, router y visibilidad por rol

**`cosecha/views.py`** + **`cosecha/urls.py`** (con `DefaultRouter`).

Cuatro `ModelViewSet`: `SupervisorViewSet`, `TrabajadorViewSet`, `CuartelViewSet`,
`RegistroCosechaViewSet`. Más adelante (11.5) sumas `AuditLogViewSet` (read-only, solo admin).

### Visibilidad por rol — `get_queryset()` dinámico

Esta es la parte difícil. El filtrado **no** es opcional ni cosmético: si un supervisor
pide `/api/trabajadores/`, la BD nunca debe devolverle trabajadores de otra cuadrilla.

| Recurso          | admin | supervisor                             | trabajador                     |
| ---------------- | ----- | -------------------------------------- | ------------------------------ |
| `trabajadores` | todos | `supervisor.usuario == request.user` | solo él mismo                 |
| `cuarteles`    | todos | los suyos                              | los de su supervisor (lectura) |
| `registros`    | todos | los de su cuadrilla                    | solo los propios               |
| `supervisores` | todos | solo su propio registro                | — (403)                       |

> Las cadenas de filtro cruzan relaciones: por ejemplo, los registros visibles para un
> supervisor son `RegistroCosecha.objects.filter(trabajador__supervisor__usuario=user)`.
> Usa `select_related`/`prefetch_related` para que esos accesos no exploten en N+1.

### Permisos por acción — `get_permissions()`

- `Supervisor`/`Cuartel`: crear/editar/borrar solo **admin**; leer admin+supervisor.
- `Trabajador`: crear/editar solo admin (un supervisor **no** crea trabajadores en esta
  versión); leer según la tabla.
- `RegistroCosecha`: crear/editar admin o supervisor (de su cuadrilla); el **trabajador es
  read-only**. `destroy` solo admin.
- Si un supervisor intenta tocar un registro/objeto de otra cuadrilla → **403** (válidalo en
  `get_object()`, no solo en el queryset de lista).

### Endpoints custom (`@action`) — mínimo 3

```text
GET  /api/registros/resumen/                  (admin/supervisor)
     → kilos totales, horas totales, rendimiento promedio, por calidad,
       y top 5 trabajadores por kilos. Todo con aggregate()/annotate(), nada en Python.

GET  /api/trabajadores/<rut>/rendimiento/      (según visibilidad)
     → kilos totales, horas, kg/hora, mejor cuartel, evolución por fecha.

GET  /api/cuarteles/<nombre>/productividad/    (admin/supervisor)
     → kg/hectárea, cosecheros distintos, kilos por calidad.
```

Filtros por query param donde corresponda: registros por `?trabajador_rut=`, `?cuartel=`,
`?calidad=`, `?desde=`, `?hasta=`; trabajadores por `?supervisor_rut=`, `?activo=`,
`?buscar=`.

---

# Tarea 11.5 — Auditoría

**`cosecha/audit.py`** — helper `registrar_audit(usuario, accion, modelo, objeto_id, descripcion, datos_previos, datos_nuevos)`.

Audita como mínimo: `crear_registro`, `editar_registro`, `eliminar_registro`,
`crear_trabajador`, `desactivar_trabajador`. En las ediciones, `datos_previos` se captura
**antes** del `.save()` y `datos_nuevos` después (sí, es el bug 5 de la Tarea 10 — no lo
repitas).

`AuditLogViewSet` (`ReadOnlyModelViewSet`, solo **admin**) con filtros `?usuario=`,
`?accion=`, `?modelo=`, `?desde=`, `?hasta=`. Regístralo en el router.

---

# Tarea 11.6 — Producción mínima: salud, CORS, paginación, env

### Endpoint público de salud

```text
GET /api/health/      (AllowAny — el único endpoint sin token)
```

Devuelve `{"status": "ok", "version": "1.0.0", "supervisores": N, "trabajadores": N, "cuarteles": N, "registros": N}`. **Lo usa el frontend (Tarea 11.10) para probar la
conexión sin necesidad de login.**

### CORS

`django-cors-headers`, `CorsMiddleware` antes de `CommonMiddleware`,
`CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']`,
`CORS_ALLOW_CREDENTIALS = True`. Pruébalo con un `OPTIONS` por curl y verifica el header
`Access-Control-Allow-Origin`.

### Paginación

`PageNumberPagination`, `PAGE_SIZE = 20`, con `page_size_query_param` y `max_page_size`.
Toda lista paginada (`{count, next, previous, results}`).

### `.env` obligatorio

`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, credenciales de BD → `config(...)` con
`python-decouple`. Entrega `backend/.env.example` con las **claves pero sin valores reales**.
`.env` al `.gitignore`.

---

# Tarea 11.7 — Datos de prueba

**`cosecha/management/commands/poblar_datos.py`** (comando, no script suelto).
Idempotente (`get_or_create`). Crea:

- 3 grupos: `admin`, `supervisor`, `trabajador`.
- 1 usuario admin (`admin_huerto` / contraseña en el comando, documentada en README).
- 4 supervisores (cada uno con su `User` y grupo), 1 inactivo.
- 20 trabajadores repartidos en las cuadrillas (cada supervisor con ≥3), al menos 3 con
  `User` propio para probar el rol `trabajador`.
- 12 cuarteles repartidos entre supervisores.
- ~400 registros de cosecha en los últimos 30 días, **respetando** la regla cruzada
  (trabajador y cuartel del mismo supervisor) y la unicidad por día.

Al final, imprime un resumen tabulado de lo creado.

---

# Tarea 11.8 — `pruebas_api.http`

Mínimo 18 requests cubriendo: health (sin token), login de los 3 roles, `/auth/me/` por rol,
listados filtrados por rol (demostrando que cada uno ve **solo lo suyo**), creación de
registro válido (201), registro inválido por regla cruzada (400), registro duplicado del
mismo día (400/409), un supervisor tocando datos de otra cuadrilla (403), trabajador
intentando un POST (403), los 3 `@action` de métricas, y la auditoría (admin sí, otros 403).

Anota el código de respuesta real junto a cada `###`.

---

# Tarea 11.9 — Tests automatizados (esto sube el listón)

**`cosecha/tests.py`** — `APITestCase` de DRF. **Mínimo 10 tests** que cubran:

- Login devuelve token; request sin token → 401.
- `get_queryset` por rol: el supervisor A **no** ve trabajadores/registros del supervisor B.
- Trabajador ve solo sus registros.
- Creación válida de registro → 201; regla cruzada inválida → 400; duplicado por día → 400/409.
- Trabajador haciendo POST a registros → 403.
- Supervisor completando/editando un registro de otra cuadrilla → 403.
- `/api/audit-logs/` accesible solo para admin (otros → 403).
- Cada edición de registro deja un `AuditLog` con `datos_previos`/`datos_nuevos` correctos.

```bash
python manage.py test cosecha
```

Todos en verde antes del commit.

---

# Tarea 11.10 — Next.js: solo scaffolding + un fetch

> Esta parte es deliberadamente chica. Hoy **no** hay login ni pantallas: solo dejar el
> frontend creado y demostrar que habla con el backend. El login y los listados son de la
> Tarea 12.

### 11.10.1 — Crear el proyecto

```bash
cd Res-Tarea-11/frontend
npx create-next-app@latest campo-web
```

Elige: **TypeScript sí**, **Tailwind sí**, **App Router sí**, **src/ a tu gusto**,
**ESLint sí**. Sin Docker.

### 11.10.2 — Cliente de API

**`frontend/campo-web/lib/api.ts`** — una función mínima:

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api';

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health/`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`API respondió ${res.status}`);
  return res.json();
}
```

**`frontend/campo-web/.env.local.example`**:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

(`.env.local` real va al `.gitignore`.)

### 11.10.3 — Una sola página que prueba la conexión

**`app/page.tsx`** — un Server Component que llama a `getHealth()` y muestra el estado y
los contadores que devuelve `/api/health/`. Si la API está caída, muestra un mensaje de error
claro (no una pantalla en blanco). Eso es todo el frontend de hoy.

Verifícalo: con el backend corriendo en `:8000` y `npm run dev` en `:3000`, abrir
`http://localhost:3000` debe mostrar los contadores reales del backend. Eso prueba que el
monorepo full-stack está conectado de punta a punta.

---

## Reglas obligatorias (resumen)

1. **Backend desde cero** — nada copiado del Taller. Dominio de campo nuevo.
2. **Visibilidad por rol real** en `get_queryset()` y `get_object()` — no se filtra en el frontend, se filtra en la BD.
3. **Serializers separados** lectura/escritura; sin referencias circulares.
4. **Sin N+1**: `select_related`/`prefetch_related` donde toque.
5. **Auditoría** con `datos_previos`/`datos_nuevos` correctos.
6. **Tests en verde** (`python manage.py test cosecha`).
7. **Frontend mínimo** pero **conectado** (`/api/health/` visible en la home).

---

## Verificaciones antes del commit

- [ ] `python manage.py migrate` y `poblar_datos` corren sin error y son idempotentes.
- [ ] `GET /api/health/` responde **sin** token con los contadores.
- [ ] Cualquier otro endpoint sin token → **401**.
- [ ] `admin_huerto` ve todos los trabajadores/cuarteles/registros.
- [ ] Supervisor A ve **solo** su cuadrilla; no ve nada de B (verificado por dato, no por UI).
- [ ] Trabajador ve **solo** sus registros; POST a registros → 403.
- [ ] Registro con cuartel de otra cuadrilla → 400 con mensaje de la regla cruzada.
- [ ] Registro duplicado (mismo trabajador/cuartel/fecha) → rechazado.
- [ ] Supervisor tocando un registro de otra cuadrilla → 403.
- [ ] Los 3 `@action` de métricas devuelven agregados correctos (sin loops en Python).
- [ ] `GET /api/audit-logs/` solo admin; ediciones dejan `datos_previos`/`datos_nuevos` ok.
- [ ] `python manage.py test cosecha` → todos verdes.
- [ ] CORS: `OPTIONS` desde `localhost:3000` trae `Access-Control-Allow-Origin`.
- [ ] `http://localhost:3000` muestra los contadores reales del backend.
- [ ] `.env` y `.env.local` **no** están en el repo; sí están sus `.example`.

---

## Entrega

```
Res-Tarea-11/
├── backend/
│   ├── proyecto_django/
│   │   ├── manage.py
│   │   ├── campo/{settings.py, urls.py}
│   │   └── cosecha/{models, serializers, views, urls, permissions,
│   │                pagination, audit, tests, management/commands/poblar_datos}
│   ├── pruebas_api.http
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── campo-web/{lib/api.ts, app/page.tsx, .env.local.example, ...}
└── README.md   ← cómo levantar backend y frontend desde cero, credenciales de los 3 roles
```
