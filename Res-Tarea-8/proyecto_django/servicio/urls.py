#aca todos los endpoints estaban ingresados manualmente, pero ahora se utilizara Router
#Router genera las URLs automaticamente para ViewSets, detectara @action y crea rutas custom automaticamente

#Router = genera URLs automáticamente para ViewSets
from rest_framework.routers import DefaultRouter

from . import views

from .views import AuditLogViewSet


#DefaultRouter crea automáticamente las rutas CRUD
router = DefaultRouter()


#register conecta una URL con un ViewSet
router.register(
    'mecanicos',
    views.MecanicoViewSet,
    basename='mecanico'
)

#register conecta automáticamente URLs CRUD
router.register(
    'clientes',
    views.ClienteViewSet,
    basename='cliente'
)

#register conecta URLs automáticas para ViewSets
router.register(
    'vehiculos',
    views.VehiculoViewSet,
    basename='vehiculo'
)

#register conecta automáticamente URLs CRUD
router.register(
    'ordenes',
    views.OrdenViewSet,
    basename='orden'
)

#audit logs, historial de la auditoria del sistema
router.register(
    r'audit-logs',
    AuditLogViewSet,
    basename='audit-log'
)

#router.urls contiene todas las URLs generadas automáticamente
urlpatterns = router.urls
