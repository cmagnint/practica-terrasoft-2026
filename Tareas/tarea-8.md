# 📘 Tarea 8 — API lista para producción

> **Esta tarea es la última de backend.** A partir de la próxima semana empezamos a consumir esta API desde Next.js. Todo lo que dejes bien acá te ahorra dolor después.

---

## 🛠️ Contexto

Tu API del taller mecánico funciona, pero hoy **cualquiera puede hacer cualquier cosa**: crear órdenes, modificar clientes, ver todos los vehículos. En producción esto no existe.

> *"Mira, el sistema lo van a usar tres personas distintas: yo como dueño, los mecánicos, y los clientes que quieren ver el estado de su auto desde el celular. No quiero que un cliente entre a editar las órdenes, ni que un mecánico vea la información personal de los clientes. Cada uno ve lo suyo y nada más. Y otra cosa — necesito un registro de todo lo que pasa: quién marcó completada una orden, quién cambió el monto, todo. Si algo sale mal quiero saber a quién preguntarle."*

**Reutilizas el proyecto del Taller (Tarea 7).** Copia la carpeta a `Res-Tarea-8/`.

---

## 📋 Estructura: 4 tareas independientes

Esta entrega se divide en **4 tareas independientes pero acumulativas**. No tienen días fijos asignados — avanza a tu ritmo. Cada tarea tiene su commit propio.

| Tarea | Tema | Concepto principal |
|-------|------|--------------------|
| 8.1 | Refactor a ViewSets + Router | Patrón estándar de DRF, `@action`, custom routes |
| 8.2 | Autenticación JWT | Tokens, login/refresh/verify, `IsAuthenticated` |
| 8.3 | Permisos por rol + AuditLog | Custom permissions, `get_queryset()` dinámico, registro de auditoría |
| 8.4 | CORS + paginación + documentación | Preparación para frontend |

> ⚠️ **Cada tarea tiene su propio commit.** No esperes a terminar todo para subir el primero. Si te atascas en la 8.3, ya tienes 8.1 y 8.2 en el repo.

---
---

# 🧩 Tarea 8.1 — Refactor a ViewSets + Router

## 🧠 Concepto: qué es un ViewSet

Hasta ahora cada endpoint era una clase APIView con sus métodos `get`, `post`, `patch`. Con ViewSet defines **una sola clase por recurso** y DRF mapea los métodos HTTP automáticamente:

```
APIView (lo que tienes hoy)            ViewSet (lo que vas a tener)
─────────────────────────────          ─────────────────────────────
class ClienteListView(APIView):        class ClienteViewSet(viewsets.ModelViewSet):
    def get(...)                           def list(...)
    def post(...)                          def create(...)
                                           def retrieve(...)
class ClienteDetailView(APIView):          def update(...)
    def get(...)                           def partial_update(...)
                                           def destroy(...)
```

El **Router** genera las URLs automáticamente:

```python
router.register('clientes', ClienteViewSet)
# Esto crea:
#   GET    /clientes/         → list()
#   POST   /clientes/         → create()
#   GET    /clientes/<pk>/    → retrieve()
#   PUT    /clientes/<pk>/    → update()
#   PATCH  /clientes/<pk>/    → partial_update()
#   DELETE /clientes/<pk>/    → destroy()
```

Y el decorador `@action` te permite agregar endpoints custom sin salirte del ViewSet:

```python
@action(detail=True, methods=['post'])
def activar(self, request, pk=None):
    # POST /clientes/<pk>/activar/
    ...
```

---

## 📋 Lo que debes hacer

### 8.1.1 — Crear los 4 ViewSets

📄 **Archivo:** `servicio/views.py`

Reemplaza las 8 APIViews por 4 ViewSets:

#### `MecanicoViewSet(viewsets.ModelViewSet)`

- `serializer_class = MecanicoSerializer`
- `lookup_field = 'rut'`
- `queryset = Mecanico.objects.all()`
- Override `get_queryset()` para los filtros `?activo=`, `?especialidad=`
- Override `retrieve()` para incluir `ordenes_activas` y `stats`
- **No implementes `destroy()`** — los mecánicos no se borran, se desactivan con `@action`

**Endpoints custom:**

```python
@action(detail=True, methods=['post'], url_path='desactivar')
def desactivar(self, request, rut=None):
    # POST /api/mecanicos/<rut>/desactivar/
    # Cambia activo=False, devuelve mensaje
```

```python
@action(detail=False, methods=['get'], url_path='disponibles')
def disponibles(self, request):
    # GET /api/mecanicos/disponibles/
    # Devuelve solo mecánicos activos con menos de 3 órdenes activas
```

#### `ClienteViewSet(viewsets.ModelViewSet)`

- `lookup_field = 'rut'`
- Override `get_queryset()` para filtros `?buscar=`, `?con_vehiculos=`
- Override `retrieve()` para incluir `vehiculos` anidados y `stats`

```python
@action(detail=True, methods=['get'], url_path='ordenes')
def ordenes(self, request, rut=None):
    # GET /api/clientes/<rut>/ordenes/
    # Devuelve todas las órdenes de los vehículos de ese cliente
    # Soporta ?estado= para filtrar
```

#### `VehiculoViewSet(viewsets.ModelViewSet)`

- `lookup_field = 'patente'`
- Override `get_queryset()` para filtros `?marca=`, `?cliente_rut=`, `?anio_desde=`, `?anio_hasta=`
- Override `retrieve()` para incluir cliente anidado, órdenes y stats

```python
@action(detail=True, methods=['get'], url_path='historial')
def historial(self, request, patente=None):
    # GET /api/vehiculos/<patente>/historial/
    # Todas las órdenes del vehículo ordenadas por fecha desc
    # Incluye stats: total gastado, visitas, último servicio
```

#### `OrdenViewSet(viewsets.ModelViewSet)`

- `lookup_field = 'pk'`
- Usa `get_serializer_class()` para elegir serializer según `self.action`:

```python
def get_serializer_class(self):
    if self.action == 'create':
        return OrdenTrabajoCreateSerializer
    if self.action in ['update', 'partial_update']:
        return OrdenTrabajoUpdateSerializer
    return OrdenTrabajoSerializer
```

- Override `get_queryset()` para filtros (estado, mecanico_rut, vehiculo_patente, vencidas)

**Endpoints custom:**

```python
@action(detail=True, methods=['post'], url_path='completar')
def completar(self, request, pk=None):
    # POST /api/ordenes/<pk>/completar/
    # Body: {"monto": 85000, "fecha_entrega_real": "2026-05-15"}
    # Si ya estaba completada → 400

@action(detail=True, methods=['post'], url_path='cancelar')
def cancelar(self, request, pk=None):
    # POST /api/ordenes/<pk>/cancelar/
    # Body: {"motivo": "Cliente no se presentó"}
    # Guarda el motivo en observaciones

@action(detail=False, methods=['get'], url_path='resumen')
def resumen(self, request):
    # GET /api/ordenes/resumen/
    # Métricas: total por estado, monto facturado, top 3 mecánicos
```

---

### 8.1.2 — Configurar el Router

📄 **Archivo:** `servicio/urls.py`

```python
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('mecanicos', views.MecanicoViewSet, basename='mecanico')
router.register('clientes', views.ClienteViewSet, basename='cliente')
router.register('vehiculos', views.VehiculoViewSet, basename='vehiculo')
router.register('ordenes', views.OrdenViewSet, basename='orden')

urlpatterns = router.urls
```

> 💡 `basename` es obligatorio cuando defines `queryset` con un override.

---

## ✅ Verificaciones 8.1

- [ ] El servidor levanta sin errores.
- [ ] `GET /api/mecanicos/` devuelve la lista.
- [ ] `GET /api/mecanicos/<rut>/` devuelve detalle con `ordenes_activas` y `stats`.
- [ ] `POST /api/mecanicos/<rut>/desactivar/` cambia `activo` a `False`.
- [ ] `GET /api/mecanicos/disponibles/` devuelve solo mecánicos activos con <3 órdenes.
- [ ] `GET /api/clientes/<rut>/ordenes/` devuelve las órdenes del cliente.
- [ ] `POST /api/ordenes/<id>/completar/` marca como Completada.
- [ ] `POST /api/ordenes/<id>/cancelar/` marca como Cancelada.
- [ ] `GET /api/ordenes/resumen/` devuelve métricas con top 3 mecánicos.

**Commit:**
```bash
git add proyecto_django/servicio/views.py proyecto_django/servicio/urls.py
git commit -m "tarea 08.1 - refactor a viewsets y router"
git push
```

---
---

# 🧩 Tarea 8.2 — Autenticación JWT

## 🧠 Concepto: por qué JWT

Hoy cualquiera puede hacer `POST /api/ordenes/` y crear órdenes sin identificarse. En producción cada request debe traer una prueba de que el usuario está autenticado.

**JWT (JSON Web Token)** es un string firmado criptográficamente que el servidor genera cuando el usuario hace login. El cliente lo guarda y lo envía en cada request:

```
1. POST /api/auth/login/   {username, password}
   ← respuesta: {access: "eyJ...", refresh: "eyJ..."}

2. GET /api/ordenes/
   Header: Authorization: Bearer eyJ...
   ← respuesta: lista de órdenes
```

El servidor **no guarda el token en BD** — lo valida criptográficamente cada vez. Por eso es escalable.

---

## 📋 Lo que debes hacer

### 8.2.1 — Instalar simplejwt

```bash
pip install djangorestframework-simplejwt
```

Agrega al `requirements.txt`.

📄 **`settings.py`:**

```python
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [...],
    'DEFAULT_PARSER_CLASSES': [...],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

> ⚠️ Una vez que actives `IsAuthenticated` como default, **todos** los endpoints requieren token.

---

### 8.2.2 — Endpoints de autenticación

📄 **`taller/urls.py`:**

```python
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('servicio.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
```

| Endpoint | Body | Devuelve |
|----------|------|----------|
| `POST /api/auth/login/` | `{username, password}` | `{access, refresh}` |
| `POST /api/auth/refresh/` | `{refresh}` | `{access}` nuevo |
| `POST /api/auth/verify/` | `{token}` | `200 OK` si válido, `401` si no |

---

### 8.2.3 — Crear los usuarios de prueba

📄 **Extender `poblar_datos.py`:**

```python
from django.contrib.auth.models import User

admin_user, _ = User.objects.get_or_create(
    username='admin_taller',
    defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@taller.cl'}
)
admin_user.set_password('admin123')
admin_user.save()

mec_user, _ = User.objects.get_or_create(
    username='carlos_munoz',
    defaults={'email': 'carlos@taller.cl'}
)
mec_user.set_password('mecanico123')
mec_user.save()

cli_user, _ = User.objects.get_or_create(
    username='juan_perez',
    defaults={'email': 'juan@gmail.com'}
)
cli_user.set_password('cliente123')
cli_user.save()
```

---

### 8.2.4 — Probar el flujo completo

```http
### LOGIN
# @name login
POST http://localhost:8000/api/auth/login/
Content-Type: application/json

{"username": "admin_taller", "password": "admin123"}

###

@accessToken = {{login.response.body.access}}

GET http://localhost:8000/api/mecanicos/
Authorization: Bearer {{accessToken}}

###

### Sin token → 401
GET http://localhost:8000/api/mecanicos/

###

### Refresh
POST http://localhost:8000/api/auth/refresh/
Content-Type: application/json

{"refresh": "{{login.response.body.refresh}}"}
```

---

## ✅ Verificaciones 8.2

- [ ] `pip show djangorestframework-simplejwt` muestra la librería instalada.
- [ ] `POST /api/auth/login/` con credenciales válidas devuelve `{access, refresh}`.
- [ ] `POST /api/auth/login/` con credenciales inválidas devuelve `401`.
- [ ] Cualquier request sin header `Authorization: Bearer` devuelve `401`.
- [ ] Cualquier request con token válido funciona como antes.
- [ ] `POST /api/auth/refresh/` con refresh válido devuelve nuevo `access`.

**Commit:**
```bash
git add proyecto_django/taller/settings.py proyecto_django/taller/urls.py
git add poblar_datos.py pruebas_api.http requirements.txt
git commit -m "tarea 08.2 - autenticacion JWT"
git push
```

---
---

# 🧩 Tarea 8.3 — Permisos por rol + AuditLog

> **Esta es la tarea más exigente del bloque.** Te va a tomar más tiempo que las otras tres. No te apures, hazla con calma.

---

## 🧠 Concepto 1: roles y permisos

Hoy todos los usuarios autenticados pueden hacer todo. Necesitamos **3 roles**:

| Rol | Qué puede hacer |
|-----|----------------|
| **admin** | Todo. Ve los 20 clientes, los 35 vehículos, las 60 órdenes. CRUD completo. |
| **mecanico** | Ve solo **sus** órdenes asignadas. Puede actualizar el estado de sus órdenes. No ve datos personales completos de clientes. |
| **cliente** | Ve solo **sus** vehículos y **sus** órdenes. No puede crear ni borrar nada — solo lectura. |

DRF tiene dos mecanismos para controlar acceso:

1. **`permission_classes`** — controla **si** un usuario puede acceder a un endpoint (devuelve 403 si no).
2. **`get_queryset()` dinámico** — controla **qué** datos ve cada usuario (filtra la lista según quién consulta).

---

## 🧠 Concepto 2: AuditLog

El dueño quiere saber quién hizo qué y cuándo. Eso es **auditoría**: una tabla que registra cada acción importante.

```
AuditLog
├── usuario (FK)        — quién hizo la acción
├── accion (string)     — qué hizo: "completar_orden", "crear_cliente"...
├── modelo (string)     — sobre qué modelo: "OrdenTrabajo", "Cliente"...
├── objeto_id (int)     — id del objeto afectado
├── descripcion (text)  — descripción legible
├── datos_previos (JSON) — estado antes del cambio (opcional)
├── datos_nuevos (JSON)  — estado después del cambio
└── timestamp (datetime auto)
```

Cada vez que pasa algo importante, se crea un registro. Luego el admin puede consultar el historial.

---

## 📋 Lo que debes hacer

### 8.3.1 — Vincular User con Mecanico y Cliente

📄 **`servicio/models.py`:**

```python
from django.contrib.auth.models import User

class Mecanico(models.Model):
    # ... campos existentes ...
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mecanico'
    )

class Cliente(models.Model):
    # ... campos existentes ...
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cliente'
    )
```

---

### 8.3.2 — Crear el modelo AuditLog

📄 **`servicio/models.py`:**

```python
class AuditLog(models.Model):
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='audit_logs'
    )
    accion = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    objeto_id = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField()
    datos_previos = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.usuario.username if self.usuario else 'anonimo'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {username} — {self.accion}"
```

**Acciones que debes auditar** (lista mínima):

| Acción | Cuándo se registra |
|--------|--------------------|
| `crear_cliente` | POST /api/clientes/ exitoso |
| `actualizar_cliente` | PATCH/PUT /api/clientes/<rut>/ exitoso |
| `crear_vehiculo` | POST /api/vehiculos/ exitoso |
| `crear_orden` | POST /api/ordenes/ exitoso |
| `completar_orden` | POST /api/ordenes/<pk>/completar/ exitoso |
| `cancelar_orden` | POST /api/ordenes/<pk>/cancelar/ exitoso |
| `desactivar_mecanico` | POST /api/mecanicos/<rut>/desactivar/ exitoso |

Crea las migraciones y aplícalas.

---

### 8.3.3 — Helper para registrar audit logs

📄 **Crea `servicio/audit.py`:**

```python
from .models import AuditLog

def registrar_audit(usuario, accion, modelo, objeto_id=None,
                    descripcion='', datos_previos=None, datos_nuevos=None):
    """Helper para crear entradas de auditoría desde las views."""
    return AuditLog.objects.create(
        usuario=usuario if usuario.is_authenticated else None,
        accion=accion,
        modelo=modelo,
        objeto_id=objeto_id,
        descripcion=descripcion,
        datos_previos=datos_previos,
        datos_nuevos=datos_nuevos,
    )
```

Úsalo en cada `@action` y en cada `create()`/`update()` que corresponda:

```python
@action(detail=True, methods=['post'], url_path='completar')
def completar(self, request, pk=None):
    orden = self.get_object()
    if orden.estado == 'Completada':
        return Response({'error': 'Ya estaba completada'}, status=400)

    datos_previos = {'estado': orden.estado, 'monto': str(orden.monto) if orden.monto else None}
    orden.estado = 'Completada'
    orden.monto = request.data.get('monto')
    orden.fecha_entrega_real = request.data.get('fecha_entrega_real')
    orden.save()

    registrar_audit(
        usuario=request.user,
        accion='completar_orden',
        modelo='OrdenTrabajo',
        objeto_id=orden.id,
        descripcion=f"Orden #{orden.id} completada por {request.user.username}",
        datos_previos=datos_previos,
        datos_nuevos={'estado': 'Completada', 'monto': str(orden.monto)},
    )
    return Response(OrdenTrabajoSerializer(orden).data)
```

---

### 8.3.4 — Crear grupos y asignar usuarios

📄 **`poblar_datos.py`:**

```python
from django.contrib.auth.models import Group

admin_group, _ = Group.objects.get_or_create(name='admin')
mecanico_group, _ = Group.objects.get_or_create(name='mecanico')
cliente_group, _ = Group.objects.get_or_create(name='cliente')

admin_user.groups.add(admin_group)
mec_user.groups.add(mecanico_group)
cli_user.groups.add(cliente_group)

# Vincular Mecanico y Cliente con sus usuarios
mec = Mecanico.objects.first()
mec.usuario = mec_user
mec.save()

cli = Cliente.objects.first()
cli.usuario = cli_user
cli.save()
```

---

### 8.3.5 — Helpers y permisos personalizados

📄 **Crea `servicio/permissions.py`:**

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS

def es_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name='admin').exists()
    )

def es_mecanico(user):
    return user.is_authenticated and user.groups.filter(name='mecanico').exists()

def es_cliente(user):
    return user.is_authenticated and user.groups.filter(name='cliente').exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return es_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Admins pueden hacer todo. Otros solo GET."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return es_admin(request.user)


class IsAdminOrMecanico(BasePermission):
    def has_permission(self, request, view):
        return es_admin(request.user) or es_mecanico(request.user)
```

---

### 8.3.6 — Aplicar permisos por ViewSet

📄 **`servicio/views.py`:**

#### `MecanicoViewSet`

```python
permission_classes = [IsAdmin]

def get_permissions(self):
    if self.action == 'disponibles':
        return [IsAuthenticated()]
    return [IsAdmin()]
```

Solo admin puede gestionar mecánicos. Excepción: `disponibles/` que cualquier autenticado puede ver.

#### `ClienteViewSet`

```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    qs = Cliente.objects.all()
    user = self.request.user
    if es_cliente(user):
        qs = qs.filter(usuario=user)
    elif es_mecanico(user):
        qs = qs.filter(vehiculos__ordenes__mecanico__usuario=user).distinct()
    return qs

def get_permissions(self):
    if self.action in ['create', 'update', 'partial_update', 'destroy']:
        return [IsAdmin()]
    return [IsAuthenticated()]
```

#### `VehiculoViewSet`

```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    qs = Vehiculo.objects.all()
    user = self.request.user
    if es_cliente(user):
        qs = qs.filter(cliente__usuario=user)
    elif es_mecanico(user):
        qs = qs.filter(ordenes__mecanico__usuario=user).distinct()
    return qs

def get_permissions(self):
    if self.action == 'create':
        return [IsAuthenticated()]
    if self.action in ['update', 'partial_update', 'destroy']:
        return [IsAdmin()]
    return [IsAuthenticated()]
```

Para `create`, valida que si es cliente, el `cliente` del body sea él mismo:

```python
def create(self, request, *args, **kwargs):
    if es_cliente(request.user):
        cliente_id = request.data.get('cliente')
        if cliente_id != request.user.cliente.id:
            return Response(
                {'error': 'Solo puedes crear vehículos a tu nombre'},
                status=403
            )
    return super().create(request, *args, **kwargs)
```

#### `OrdenViewSet`

```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    qs = OrdenTrabajo.objects.all()
    user = self.request.user
    if es_cliente(user):
        qs = qs.filter(vehiculo__cliente__usuario=user)
    elif es_mecanico(user):
        qs = qs.filter(mecanico__usuario=user)
    return qs

def get_permissions(self):
    if self.action == 'create':
        return [IsAdminOrMecanico()]
    if self.action in ['update', 'partial_update', 'completar', 'cancelar']:
        return [IsAdminOrMecanico()]
    if self.action == 'destroy':
        return [IsAdmin()]
    return [IsAuthenticated()]
```

Adicional: en `update`/`completar`/`cancelar`, si es mecánico, validar que es **su** orden:

```python
def get_object(self):
    obj = super().get_object()
    user = self.request.user
    if self.action in ['update', 'partial_update', 'completar', 'cancelar']:
        if es_mecanico(user) and obj.mecanico.usuario != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Solo puedes modificar tus propias órdenes')
    return obj
```

---

### 8.3.7 — Endpoint `/api/auth/me/`

Necesario para que el frontend sepa quién está logueado y qué rol tiene.

```python
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rol = 'admin' if es_admin(user) else (
            'mecanico' if es_mecanico(user) else (
                'cliente' if es_cliente(user) else 'sin_rol'
            )
        )
        data = {
            'username': user.username,
            'email': user.email,
            'rol': rol,
        }
        if rol == 'mecanico' and hasattr(user, 'mecanico'):
            data['mecanico'] = MecanicoSerializer(user.mecanico).data
        elif rol == 'cliente' and hasattr(user, 'cliente'):
            data['cliente'] = ClienteResumenSerializer(user.cliente).data
        return Response(data)
```

En `taller/urls.py`:
```python
path('api/auth/me/', MeView.as_view(), name='me'),
```

---

### 8.3.8 — Endpoint de consulta de AuditLog

Solo accesible para admin. Permite consultar el historial.

```python
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura. Solo admin puede ver."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        params = self.request.query_params

        if usuario := params.get('usuario'):
            qs = qs.filter(usuario__username=usuario)
        if accion := params.get('accion'):
            qs = qs.filter(accion=accion)
        if modelo := params.get('modelo'):
            qs = qs.filter(modelo=modelo)
        if desde := params.get('desde'):
            qs = qs.filter(timestamp__gte=desde)
        if hasta := params.get('hasta'):
            qs = qs.filter(timestamp__lte=hasta)

        return qs
```

Crea el serializer:

```python
class AuditLogSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'usuario_username', 'accion', 'modelo',
                  'objeto_id', 'descripcion', 'datos_previos',
                  'datos_nuevos', 'timestamp']
```

Registra en el router:
```python
router.register('audit-logs', views.AuditLogViewSet, basename='auditlog')
```

---

### 8.3.9 — Probar con los 3 roles

Agrega al `.http`:

```http
### LOGIN COMO MECÁNICO
# @name loginMec
POST http://localhost:8000/api/auth/login/
{"username": "carlos_munoz", "password": "mecanico123"}

###

@tokenMec = {{loginMec.response.body.access}}

### Mecánico ve solo sus órdenes
GET http://localhost:8000/api/ordenes/
Authorization: Bearer {{tokenMec}}

### Mecánico NO puede crear cliente → 403
POST http://localhost:8000/api/clientes/
Authorization: Bearer {{tokenMec}}
Content-Type: application/json

{"nombre": "Test", "rut": "11111111-1"}

###

### LOGIN COMO CLIENTE
# @name loginCli
POST http://localhost:8000/api/auth/login/
{"username": "juan_perez", "password": "cliente123"}

@tokenCli = {{loginCli.response.body.access}}

### Cliente ve solo sus vehículos
GET http://localhost:8000/api/vehiculos/
Authorization: Bearer {{tokenCli}}

### Cliente NO puede hacer POST a /ordenes/ → 403
POST http://localhost:8000/api/ordenes/
Authorization: Bearer {{tokenCli}}

###

### Admin completa una orden (genera audit log)
POST http://localhost:8000/api/ordenes/1/completar/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{"monto": 85000, "fecha_entrega_real": "2026-05-15"}

###

### Admin consulta el audit log
GET http://localhost:8000/api/audit-logs/
Authorization: Bearer {{accessToken}}

### Audit log filtrado por acción
GET http://localhost:8000/api/audit-logs/?accion=completar_orden
Authorization: Bearer {{accessToken}}

###

### Mecánico intentando ver audit log → 403
GET http://localhost:8000/api/audit-logs/
Authorization: Bearer {{tokenMec}}
```

---

## ✅ Verificaciones 8.3

- [ ] `GET /api/auth/me/` devuelve el rol correcto para cada usuario.
- [ ] **Admin** logueado: ve los 20 clientes, los 35 vehículos, las 60 órdenes.
- [ ] **Mecánico Carlos** logueado: ve solo las órdenes asignadas a él.
- [ ] **Cliente Juan** logueado: ve solo sus propios vehículos y órdenes.
- [ ] Mecánico intentando crear cliente → 403.
- [ ] Cliente intentando hacer POST a `/ordenes/` → 403.
- [ ] Mecánico intentando completar una orden que **no** es suya → 403.
- [ ] Cada `completar`, `cancelar`, `crear_orden`, `crear_cliente` genera registro en `AuditLog`.
- [ ] `GET /api/audit-logs/` solo accesible para admin.
- [ ] `GET /api/audit-logs/?usuario=carlos_munoz` filtra correctamente.
- [ ] Los `datos_previos` y `datos_nuevos` se ven al consultar audit logs de actualización.

**Commit:**
```bash
git add proyecto_django/servicio/
git add poblar_datos.py pruebas_api.http
git commit -m "tarea 08.3 - permisos por rol y audit log"
git push
```

---
---

# 🧩 Tarea 8.4 — CORS, paginación y documentación

## 🧠 Concepto: por qué CORS

Cuando Next.js (que corre en `http://localhost:3000`) intente llamar a tu Django (en `http://localhost:8000`), **el navegador va a bloquear la request** por seguridad. Eso se llama política CORS (Cross-Origin Resource Sharing).

Django tiene que decirle al navegador "sí, acepto requests desde este origen". Eso se hace con `django-cors-headers`.

---

## 📋 Lo que debes hacer

### 8.4.1 — Configurar CORS

```bash
pip install django-cors-headers
```

📄 **`settings.py`:**

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
    'rest_framework',
    'servicio',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← AL PRINCIPIO
    'django.middleware.security.SecurityMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

> ⚠️ El orden del middleware importa. `CorsMiddleware` debe ir **antes** que `CommonMiddleware`.

Probarlo:

```bash
curl -v -X OPTIONS http://localhost:8000/api/mecanicos/ \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET"
```

Debe aparecer el header:
```
Access-Control-Allow-Origin: http://localhost:3000
```

---

### 8.4.2 — Paginación estándar

📄 **`settings.py`:**

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

Después de esto, **cualquier ViewSet automáticamente devuelve respuestas paginadas:**

```json
{
    "count": 60,
    "next": "http://localhost:8000/api/ordenes/?page=2",
    "previous": null,
    "results": [ ... 20 items ... ]
}
```

Quita el código manual de `?limite=` — ya no se necesita.

### Paginación custom

📄 **Crea `servicio/pagination.py`:**

```python
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

Cliente puede hacer `?page=2&page_size=50` para customizar.

---

### 8.4.3 — Documentación con drf-spectacular

```bash
pip install drf-spectacular
```

📄 **`settings.py`:**

```python
INSTALLED_APPS = [..., 'drf_spectacular']

REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API Taller AutoServicio',
    'DESCRIPTION': 'API REST para la gestión del taller mecánico',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

📄 **`taller/urls.py`:**

```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

Visita `http://localhost:8000/api/docs/` — vas a ver toda tu API documentada automáticamente.

### Mejorar la doc de los `@action`

```python
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Completar una orden de trabajo",
    description="Marca la orden como Completada y registra el monto final.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'monto': {'type': 'number'},
                'fecha_entrega_real': {'type': 'string', 'format': 'date'}
            },
            'required': ['monto']
        }
    },
    responses={200: OrdenTrabajoSerializer, 400: {'description': 'Validación fallida'}}
)
@action(detail=True, methods=['post'], url_path='completar')
def completar(self, request, pk=None):
    ...
```

Aplica `@extend_schema` a los 5 endpoints custom más importantes.

---

### 8.4.4 — README final del proyecto

📄 **`Res-Tarea-8/README.md`:**

Documenta:

1. **Cómo levantar el proyecto desde cero** (Docker, .env, migraciones, poblar datos).
2. **Credenciales de los 3 usuarios** de prueba.
3. **Cómo loguearse y usar el token** (ejemplo curl completo).
4. **Tabla de endpoints** principales con qué rol puede acceder a cada uno.
5. **Link a `/api/docs/`** para la documentación interactiva.

---

## ✅ Verificaciones 8.4

- [ ] El servidor levanta y `/api/docs/` muestra Swagger.
- [ ] CORS funciona: request desde `http://localhost:3000` con `curl` no es bloqueada.
- [ ] `GET /api/ordenes/` ahora devuelve `{count, next, previous, results}`.
- [ ] `GET /api/ordenes/?page=2` devuelve la segunda página.
- [ ] `GET /api/ordenes/?page=2&page_size=10` respeta el tamaño custom.
- [ ] La documentación Swagger muestra los endpoints `@action` con sus descripciones.
- [ ] El README permite que alguien que clone el repo levante el proyecto sin preguntarte nada.

**Commit:**
```bash
git add proyecto_django/ requirements.txt README.md
git commit -m "tarea 08.4 - cors paginacion y docs"
git push
```

---
---

# 🎯 Cierre del bloque backend

Cuando termines las 4 tareas, tu API debe:

- [x] Estar refactorizada a ViewSets con Router
- [x] Tener endpoints custom con `@action` claros y documentados
- [x] Requerir autenticación JWT en todos los endpoints (excepto login/refresh)
- [x] Filtrar automáticamente lo que cada rol puede ver
- [x] Registrar cada acción importante en `AuditLog`
- [x] Permitir consultar el `AuditLog` solo al admin
- [x] Aceptar requests CORS desde `localhost:3000`
- [x] Devolver respuestas paginadas estándar
- [x] Tener documentación auto-generada en `/api/docs/`
- [x] Tener un README que cualquiera puede seguir

A partir de la próxima semana **empezamos con Next.js consumiendo esta API**.

---

## 📤 Entrega final

```
Res-Tarea-8/
├── proyecto_django/
│   ├── taller/
│   │   ├── settings.py
│   │   └── urls.py
│   └── servicio/
│       ├── models.py        ← extendido con OneToOneField a User + AuditLog
│       ├── serializers.py   ← + AuditLogSerializer
│       ├── views.py         ← ViewSets + AuditLogViewSet + MeView
│       ├── urls.py          ← Router con audit-logs
│       ├── permissions.py   ← NUEVO
│       ├── pagination.py    ← NUEVO
│       ├── audit.py         ← NUEVO - helper registrar_audit()
│       └── migrations/      ← nuevas migraciones por User FK y AuditLog
├── poblar_datos.py          ← crea users + grupos + asigna usuario a Mec/Cli
├── pruebas_api.http         ← flujo de login + 3 roles + audit log
├── README.md                ← NUEVO
├── .env
└── requirements.txt
```