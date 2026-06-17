from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SupervisorViewSet,
    TrabajadorViewSet,
    CuartelViewSet,
    RegistroCosechaViewSet,
    AuditLogViewSet,
    HealthView,
)


#router principal de la app cosecha
router = DefaultRouter()

#rutas generadas automaticamente por viewsets
router.register('supervisores', SupervisorViewSet, basename='supervisor')
router.register('trabajadores', TrabajadorViewSet, basename='trabajador')
router.register('cuarteles', CuartelViewSet, basename='cuartel')
router.register('registros', RegistroCosechaViewSet, basename='registro')
router.register('audit-logs', AuditLogViewSet, basename='audit-log')


#rutas de la app cosecha
urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('', include(router.urls)),
]
