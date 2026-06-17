from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Supervisor, Trabajador, Cuartel, RegistroCosecha, AuditLog
from .permissions import es_admin, es_supervisor, es_trabajador, EsAdmin, EsAdminOSupervisor
from .serializers import (
    SupervisorSerializer,
    TrabajadorSerializer,
    CuartelSerializer,
    RegistroCosechaSerializer,
    RegistroCosechaCreateSerializer,
    AuditLogSerializer
)
from .audit import registrar_auditoria




#viewset para supervisores
class SupervisorViewSet(viewsets.ModelViewSet):
    serializer_class = SupervisorSerializer

    #filtra supervisores segun el rol del usuario
    def get_queryset(self):
        user = self.request.user

        if es_admin(user):
            return Supervisor.objects.all()

        if es_supervisor(user):
            return Supervisor.objects.filter(usuario=user)

        raise PermissionDenied('No tienes permiso para ver supervisores')


#viewset para trabajadores
class TrabajadorViewSet(viewsets.ModelViewSet):
    serializer_class = TrabajadorSerializer

    #filtra trabajadores segun el rol del usuario
    def get_queryset(self):
        user = self.request.user

        if es_admin(user):
            return Trabajador.objects.select_related('supervisor', 'usuario')

        if es_supervisor(user):
            return Trabajador.objects.select_related('supervisor', 'usuario').filter(
                supervisor__usuario=user
            )

        if es_trabajador(user):
            return Trabajador.objects.select_related('supervisor', 'usuario').filter(
                usuario=user
            )

        return Trabajador.objects.none()

    #devuelve metricas de rendimiento del trabajador
    @action(detail=True, methods=['get'])
    def rendimiento(self, request, pk=None):

        trabajador = self.get_object()

        registros = trabajador.registros.all()

        totales = registros.aggregate(
            kilos_totales=Sum('kilos'),
            horas_totales=Sum('horas')
        )

        kilos_totales = totales['kilos_totales'] or 0
        horas_totales = totales['horas_totales'] or 0

        rendimiento = 0

        if horas_totales > 0:
            rendimiento = round(
                float(kilos_totales / horas_totales),
                2
            )

        mejor_cuartel = registros.values(
            'cuartel__nombre'
        ).annotate(
            kilos=Sum('kilos')
        ).order_by('-kilos').first()

        evolucion = registros.values(
            'fecha'
        ).annotate(
            kilos=Sum('kilos')
        ).order_by('fecha')

        return Response({
            'trabajador': trabajador.nombre,
            'rut': trabajador.rut,
            'kilos_totales': kilos_totales,
            'horas_totales': horas_totales,
            'kg_por_hora': rendimiento,
            'mejor_cuartel': mejor_cuartel,
            'evolucion': list(evolucion),
        })

#viewset para cuarteles
class CuartelViewSet(viewsets.ModelViewSet):
    serializer_class = CuartelSerializer

    #filtra cuarteles segun el rol del usuario
    def get_queryset(self):
        user = self.request.user

        if es_admin(user):
            return Cuartel.objects.select_related('supervisor')

        if es_supervisor(user):
            return Cuartel.objects.select_related('supervisor').filter(
                supervisor__usuario=user
            )

        if es_trabajador(user):
            return Cuartel.objects.select_related('supervisor').filter(
                supervisor__trabajadores__usuario=user
            )

        return Cuartel.objects.none()

    #devuelve metricas de productividad del cuartel
    @action(detail=True, methods=['get'])
    def productividad(self, request, pk=None):

        cuartel = self.get_object()

        registros = cuartel.registros.all()

        totales = registros.aggregate(
            kilos_totales=Sum('kilos'),
            cosecheros_distintos=Count('trabajador', distinct=True)
        )

        kilos_totales = totales['kilos_totales'] or 0

        kg_por_hectarea = 0

        if cuartel.hectareas > 0:
            kg_por_hectarea = round(
                float(kilos_totales / cuartel.hectareas),
                2
            )

        kilos_por_calidad = registros.values(
            'calidad'
        ).annotate(
            kilos=Sum('kilos')
        ).order_by('calidad')

        return Response({
            'cuartel': cuartel.nombre,
            'hectareas': cuartel.hectareas,
            'kg_por_hectarea': kg_por_hectarea,
            'cosecheros_distintos': totales['cosecheros_distintos'],
            'kilos_por_calidad': list(kilos_por_calidad),
        })

#viewset para registros de cosecha
class RegistroCosechaViewSet(viewsets.ModelViewSet):

    #elige serializer de lectura o escritura
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RegistroCosechaCreateSerializer

        return RegistroCosechaSerializer

    #filtra registros segun el rol del usuario
    def get_queryset(self):
        user = self.request.user

        queryset = RegistroCosecha.objects.select_related(
            'trabajador',
            'trabajador__supervisor',
            'cuartel',
            'cuartel__supervisor'
        )

        if es_admin(user):
            return queryset

        if es_supervisor(user):
            return queryset.filter(
                trabajador__supervisor__usuario=user
            )

        if es_trabajador(user):
            return queryset.filter(
                trabajador__usuario=user
            )

        return RegistroCosecha.objects.none()

    #valida acceso a un registro individual
    def get_object(self):

        obj = super().get_object()
        user = self.request.user

        #admin puede acceder a cualquier registro
        if es_admin(user):
            return obj

        #supervisor solo puede acceder a su cuadrilla
        if es_supervisor(user):

            if obj.trabajador.supervisor.usuario != user:
                raise PermissionDenied(
                    'No puedes acceder a registros de otra cuadrilla'
                )

            return obj

        #trabajador solo puede acceder a sus registros
        if es_trabajador(user):

            if obj.trabajador.usuario != user:
                raise PermissionDenied(
                    'No puedes acceder a registros de otro trabajador'
                )

            return obj

        raise PermissionDenied('Acceso denegado')

    #registra auditoria al crear un registro
    def perform_create(self, serializer):
        registro = serializer.save()

        registrar_auditoria(
            usuario=self.request.user,
            accion='crear_registro',
            modelo='RegistroCosecha',
            objeto_id=registro.id,
            descripcion='se creo un registro de cosecha',
            datos_previos=None,
            datos_nuevos={
                'trabajador': registro.trabajador_id,
                'cuartel': registro.cuartel_id,
                'fecha': str(registro.fecha),
                'kilos': str(registro.kilos),
                'horas': str(registro.horas),
                'calidad': registro.calidad,
            }
        )

    #registramos la auditoria al editar un registro
    def perfom_update(self, serializer):
        registro_anterior = self.get_object()

        datos_previos = {
            'trabajador': registro_anterior.trabajador_id,
            'cuartel': registro_anterior.cuartel_id,
            'fecha': str(registro_anterior.fecha),
            'kilos': str(registro_anterior.kilos),
            'horas': str(registro_anterior.horas),
            'calidad': registro_anterior.calidad,
        }

        registro = serializer.save()

        registrar_auditoria(
            usuario=self.request.user,
            accion='editar_registro',
            modelo='RegistroCosecha',
            objeto_id=registro.id,
            descripcion='se edito un registro de cosecha',
            datos_previos=datos_previos,
            datos_nuevos={
                'trabajador': registro.trabajador_id,
                'cuartel': registro.cuartel_id,
                'fecha': str(registro.fecha),
                'kilos': str(registro.kilos),
                'horas': str(registro.horas),
                'calidad': registro.calidad,
            }
        )

    #registra auditoria al eliminar un registro
    def perform_destroy(self, instance):
        datos_previos = {
            'trabajador': instance.trabajador_id,
            'cuartel': instance.cuartel_id,
            'fecha': str(instance.fecha),
            'kilos': str(instance.kilos),
            'horas': str(instance.horas),
            'calidad': instance.calidad,
        }

        registro_id = instance.id
        instance.delete()

        registrar_auditoria(
            usuario=self.request.user,
            accion='eliminar_registro',
            modelo='RegistroCosecha',
            objeto_id=registro_id,
            descripcion='se elimino un registro de cosecha',
            datos_previos=datos_previos,
            datos_nuevos=None
        )

            #devuelve resumen general de registros visibles
    @action(detail=False, methods=['get'])
    def resumen(self, request):

        queryset = self.get_queryset()

        #calcula totales generales
        totales = queryset.aggregate(
            kilos_totales=Sum('kilos'),
            horas_totales=Sum('horas')
        )

        kilos_totales = totales['kilos_totales'] or 0
        horas_totales = totales['horas_totales'] or 0

        #calcula rendimiento promedio general
        rendimiento_promedio = 0

        if horas_totales > 0:
            rendimiento_promedio = round(
                float(kilos_totales / horas_totales),
                2
            )

        #agrupa kilos por calidad
        por_calidad = queryset.values(
            'calidad'
        ).annotate(
            kilos=Sum('kilos')
        ).order_by('calidad')

        #obtiene top 5 trabajadores por kilos
        top_trabajadores = queryset.values(
            'trabajador__id',
            'trabajador__nombre',
            'trabajador__rut'
        ).annotate(
            kilos=Sum('kilos')
        ).order_by('-kilos')[:5]

        return Response({
            'kilos_totales': kilos_totales,
            'horas_totales': horas_totales,
            'rendimiento_promedio': rendimiento_promedio,
            'por_calidad': list(por_calidad),
            'top_trabajadores': list(top_trabajadores),
        })

        #define permisos segun la accion solicitada
    def get_permissions(self):

        #solo admin puede eliminar
        if self.action == 'destroy':
            return [EsAdmin()]

        #admin y supervisor pueden crear o editar
        if self.action in [
            'create',
            'update',
            'partial_update'
        ]:
            return [EsAdminOSupervisor()]

        return super().get_permissions()

#viewset para consultar las auditorias
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = AuditLogSerializer

    #aca solo los administradores podran consultar auditorias
    def get_queryset(self):

        if not es_admin(self.request.user):
            raise PermissionDenied(
                'solo los administradores pueden acceder a las auditorias'
            )

        return AuditLog.objects.select_related(
            'usuario'
        ).order_by('-timestamp')

#vista publica para comprobar que la api funciona
class HealthView(APIView):

    #permite acceso sin token
    permission_classes = [AllowAny]

    #devuelve estado general y contadores principales
    def get(self, request):
        return Response({
            'status': 'ok',
            'version': '1.0.0',
            'supervisores': Supervisor.objects.count(),
            'trabajadores': Trabajador.objects.count(),
            'cuarteles': Cuartel.objects.count(),
            'registros': RegistroCosecha.objects.count(),
        })
