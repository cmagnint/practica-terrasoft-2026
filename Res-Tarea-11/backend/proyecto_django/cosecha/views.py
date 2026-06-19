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

    #define permisos segun la accion solicitada
    def get_permissions(self):

        #solo admin puede crear editar o eliminar supervisores
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy'
            'desactivar'
        ]:
            return [EsAdmin()]

        return super().get_permissions()

#viewset para trabajadores
class TrabajadorViewSet(viewsets.ModelViewSet):
    serializer_class = TrabajadorSerializer

    #usa el rut como identificador en la url
    lookup_field = 'rut'

    #define permisos segun la accion solicitada
    def get_permissions(self):

        #solo admin puede crear editar eliminar o desactivar trabajadores
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy',
            'desactivar'
        ]:
            return [EsAdmin()]

        return super().get_permissions()

    #filtra trabajadores segun el rol del usuario
    def get_queryset(self):
        user = self.request.user

        queryset = Trabajador.objects.select_related(
            'supervisor',
            'usuario'
        )

        if es_admin(user):
            pass

        elif es_supervisor(user):
            queryset = queryset.filter(
                supervisor__usuario=user
            )

        elif es_trabajador(user):
            queryset = queryset.filter(
                usuario=user
            )

        else:
            return Trabajador.objects.none()

        #filtra por rut del supervisor
        supervisor_rut = self.request.query_params.get('supervisor_rut')

        if supervisor_rut:
            queryset = queryset.filter(
                supervisor__rut=supervisor_rut
            )

        #filtra por estado activo
        activo = self.request.query_params.get('activo')

        if activo is not None:
            queryset = queryset.filter(
                activo=activo.lower() == 'true'
            )

        #filtra por busqueda de nombre o rut
        buscar = self.request.query_params.get('buscar')

        if buscar:
            queryset = queryset.filter(
                nombre__icontains=buscar
            ) | queryset.filter(
                rut__icontains=buscar
            )

        return queryset

    #registra auditoria al crear un trabajador
    def perform_create(self, serializer):
        trabajador = serializer.save()

        registrar_auditoria(
            usuario=self.request.user,
            accion='crear_trabajador',
            modelo='Trabajador',
            objeto_id=trabajador.id,
            descripcion='se creo un trabajador',
            datos_previos=None,
            datos_nuevos={
                'nombre': trabajador.nombre,
                'rut': trabajador.rut,
                'activo': trabajador.activo,
                'supervisor': trabajador.supervisor_id,
            }
        )

    #desactiva un trabajador sin eliminarlo
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        trabajador = self.get_object()

        datos_previos = {
            'nombre': trabajador.nombre,
            'rut': trabajador.rut,
            'activo': trabajador.activo,
            'supervisor': trabajador.supervisor_id,
        }

        trabajador.activo = False
        trabajador.save()

        registrar_auditoria(
            usuario=request.user,
            accion='desactivar_trabajador',
            modelo='Trabajador',
            objeto_id=trabajador.id,
            descripcion='se desactivo un trabajador',
            datos_previos=datos_previos,
            datos_nuevos={
                'nombre': trabajador.nombre,
                'rut': trabajador.rut,
                'activo': trabajador.activo,
                'supervisor': trabajador.supervisor_id,
            }
        )

        return Response({
            'mensaje': 'Trabajador desactivado correctamente'
        })

    #devuelve metricas de rendimiento del trabajador
    @action(detail=True, methods=['get'])
    def rendimiento(self, request, rut=None):

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

    #usa el nombre como identificador en la url
    lookup_field = 'nombre'

        #define permisos segun la accion solicitada
    def get_permissions(self):

        #solo admin puede crear editar o eliminar cuarteles
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy'
        ]:
            return [EsAdmin()]

        return super().get_permissions()

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
    def productividad(self, request, nombre=None):

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

    #define permisos segun la accion solicitada
    def get_permissions(self):

        #solo admin puede eliminar
        if self.action == 'destroy':
            return [EsAdmin()]

        #admin y supervisor pueden crear editar o ver resumen
        if self.action in [
            'create',
            'update',
            'partial_update',
            'resumen'
        ]:
            return [EsAdminOSupervisor()]

        return super().get_permissions()

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
            pass

        elif es_supervisor(user):
            queryset = queryset.filter(
                trabajador__supervisor__usuario=user
            )

        elif es_trabajador(user):
            queryset = queryset.filter(
                trabajador__usuario=user
            )

        else:
            return RegistroCosecha.objects.none()

        #filtra por rut del trabajador
        trabajador_rut = self.request.query_params.get('trabajador_rut')

        if trabajador_rut:
            queryset = queryset.filter(
                trabajador__rut=trabajador_rut
            )

        #filtra por nombre del cuartel
        cuartel = self.request.query_params.get('cuartel')

        if cuartel:
            queryset = queryset.filter(
                cuartel__nombre__icontains=cuartel
            )

        #filtra por calidad de cosecha
        calidad = self.request.query_params.get('calidad')

        if calidad:
            queryset = queryset.filter(
                calidad=calidad
            )

        #filtra desde una fecha inicial
        desde = self.request.query_params.get('desde')

        if desde:
            queryset = queryset.filter(
                fecha__gte=desde
            )

        #filtra hasta una fecha final
        hasta = self.request.query_params.get('hasta')

        if hasta:
            queryset = queryset.filter(
                fecha__lte=hasta
            )

        return queryset

    #valida acceso a un registro individual
    def get_object(self):

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        objeto_id = self.kwargs.get(lookup_url_kwarg)

        obj = RegistroCosecha.objects.select_related(
            'trabajador',
            'trabajador__supervisor',
            'cuartel',
            'cuartel__supervisor'
        ).get(pk=objeto_id)

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

    #registra auditoria al editar un registro
    def perform_update(self, serializer):
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

#viewset para consultar las auditorias
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = AuditLogSerializer

        #filtra auditorias segun parametros de busqueda
    def get_queryset(self):

        if not es_admin(self.request.user):
            raise PermissionDenied(
                'Solo los administradores pueden acceder a auditorias'
            )

        queryset = AuditLog.objects.select_related(
            'usuario'
        ).order_by('-timestamp')

        #filtra por nombre de usuario
        usuario = self.request.query_params.get('usuario')

        if usuario:
            queryset = queryset.filter(
                usuario__username__icontains=usuario
            )

        #filtra por accion realizada
        accion = self.request.query_params.get('accion')

        if accion:
            queryset = queryset.filter(
                accion__icontains=accion
            )

        #filtra por modelo afectado
        modelo = self.request.query_params.get('modelo')

        if modelo:
            queryset = queryset.filter(
                modelo__icontains=modelo
            )

        #filtra desde una fecha inicial
        desde = self.request.query_params.get('desde')

        if desde:
            queryset = queryset.filter(
                timestamp__date__gte=desde
            )

        #filtra hasta una fecha final
        hasta = self.request.query_params.get('hasta')

        if hasta:
            queryset = queryset.filter(
                timestamp__date__lte=hasta
            )

        return queryset

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
