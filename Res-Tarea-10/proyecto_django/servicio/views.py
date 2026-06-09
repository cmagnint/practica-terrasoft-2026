# Create your views here.
import logging

from django.db.models import Sum, Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import registrar_auditoria

from .models import (
    Mecanico,
    Cliente,
    Vehiculo,
    OrdenTrabajo,
    AuditLog,
    RepuestoOrden
)

from .serializers import (
    MecanicoSerializer,
    ClienteSerializer,
    ClienteResumenSerializer,
    VehiculoSerializer,
    VehiculoCreateSerializer,
    OrdenTrabajoSerializer,
    OrdenTrabajoCreateSerializer,
    OrdenTrabajoUpdateSerializer,
    AuditLogSerializer,
    RepuestoOrdenSerializer
)

from .permissions import (
    EsAdministrador,
    EsAdministradorOMecanico,
    es_admin,
    es_mecanico,
    es_cliente
)

#logger propio de la app servicio
logger = logging.getLogger('servicio')

"""MODIFICACIONES NUEVAS"""

class MecanicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar los mecanicos """

    serializer_class = MecanicoSerializer
    lookup_field = 'rut'

    def get_permissions(self):

        #disponibles puede verlo cualquier usuario autenticado
        if self.action == 'disponibles':

            return [IsAuthenticated()]

        return [EsAdministrador()]

    def get_queryset(self):

        logger.debug(
            f"{self.request.method} {self.request.path}"
            f"params={self.request.query_params}"
        )

        #anota cantidad de ordenes para evitar consultas repetidas
        mecanicos = Mecanico.objects.annotate(
            total_ordenes_anotado=Count('ordenes')
        )

        activo = self.request.query_params.get('activo')

        if activo is not None:

            mecanicos = mecanicos.filter(
                activo=activo.lower() == 'true'
            )

        especialidad = self.request.query_params.get('especialidad')

        if especialidad:

            mecanicos = mecanicos.filter(
                especialidad=especialidad
            )

        return mecanicos

    def retrieve(self, request, *args, **kwargs):
        """Esto devuelve el detalle de un mecanico con sus ordenes activas y estadisticas"""

        logger.debug(
            f"{request.method} {request.path}"
        )

        mecanico = self.get_object()

        #select_related optimiza las consultas Sql con FK
        ordenes_activas = (
            mecanico.ordenes
            .select_related('vehiculo', 'mecanico')
            .filter(
                estado__in=[
                    'Pendiente',
                    'En progreso'
                ]
            )
        )

        ordenes_completadas = mecanico.ordenes.filter(
            estado='Completada'
        ).count()

        ordenes_canceladas = mecanico.ordenes.filter(
            estado='Cancelada'
        ).count()

        monto_total = mecanico.ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "mecanico": MecanicoSerializer(
                mecanico
            ).data,

            "ordenes_activas": OrdenTrabajoSerializer(
                ordenes_activas,
                many=True
            ).data,

            "stats": {
                "ordenes_completadas": ordenes_completadas,
                "ordenes_canceladas": ordenes_canceladas,
                "monto_total_facturado": monto_total
            }

        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):

        #los mecanicos no se eliminan
        raise MethodNotAllowed('DELETE')

    @extend_schema(
        summary="Desactivar mecanico",
        description="Desactiva un mecanico sin eliminarlo de la base de datos.",
        responses={200: MecanicoSerializer}
    )
    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, rut=None):
        #action es como un endpoint personalizado dentro de un ViewSet
        #detail=True significa que trabaja sobre un mecanico específico

        mecanico = self.get_object()

        datos_previos = {
            'activo': mecanico.activo
        }

        mecanico.activo = False
        mecanico.save()

        registrar_auditoria(
            usuario=request.user,
            accion='desactivar_mecanico',
            modelo='Mecanico',
            descripcion=f'Mecanico {mecanico.rut} desactivado',
            objeto_id=mecanico.id,
            datos_previos=datos_previos,
            datos_nuevos={
                'activo': mecanico.activo
            }
        )

        return Response({
            "mensaje": "Mecánico desactivado correctamente",
            "mecanico": MecanicoSerializer(mecanico).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mecanicos disponibles",
        description="Devuelve solo mecanicos activos con menos de 3 ordenes activas.",
        responses={200: MecanicoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        #detail=False significa que no usa un rut especifico

        #calcula ordenes activas desde la base de datos
        mecanicos = Mecanico.objects.filter(
            activo=True
        ).annotate(
            ordenes_activas_count=Count(
                'ordenes',
                filter=Q(
                    ordenes__estado__in=[
                        'Pendiente',
                        'En progreso'
                    ]
                )
            ),
            total_ordenes_anotado=Count('ordenes')
        ).filter(
            ordenes_activas_count__gte=3
        )

        serializer = MecanicoSerializer(
            mecanicos,
            many=True
        )

        return Response({
            "total": mecanicos.count(),
            "mecanicos": serializer.data
        }, status=status.HTTP_200_OK)

class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet actualizado par gestionar clientes"""

    permission_classes = [IsAuthenticated]

    serializer_class = ClienteSerializer
    lookup_field = 'rut'

    def get_permissions(self):

        #solo admin puede modificar clientes
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy'
        ]:

            return [EsAdministrador()]

        return [IsAuthenticated()]

    def get_queryset(self):

        logger.debug(
            f"{self.request.method} {self.request.path} "
            f"params={self.request.query_params}"
        )

        clientes = Cliente.objects.prefetch_related( #patch_related optimiza relaciones MTM o reverse fk
            'vehiculos'
        )

        user = self.request.user

        #cliente solo ve su propio registro
        if es_cliente(user):

            clientes = clientes.filter(
                usuario=user
            )

        #mecanico solo ve clientes con ordenes asignadas a el
        elif es_mecanico(user):

            clientes = clientes.filter(
                vehiculos__ordenes__mecanico__usuario=user
            ).distinct()

        buscar = self.request.query_params.get('buscar')

        if buscar:

            clientes = clientes.filter(
                nombre__icontains=buscar
            )

#filtro clientes con vehículos
        con_vehiculos = self.request.query_params.get(
            'con_vehiculos'
        )

        if con_vehiculos == 'true':
            clientes = clientes.filter(
                vehiculos__isnull=False
            ).distinct()

        return clientes

    def create(self, request, *args, **kwargs):

        response = super().create(request, *args, **kwargs)

        registrar_auditoria(
            usuario=request.user,
            accion='crear_cliente',
            modelo='Cliente',
            descripcion='Cliente creado',
            objeto_id=response.data.get('id'),
            datos_nuevos=response.data
        )

        return response

    def update(self, request, *args, **kwargs):

        cliente = self.get_object()

        datos_previos = ClienteSerializer(
            cliente
        ).data

        response = super().update(request, *args, **kwargs)

        registrar_auditoria(
            usuario=request.user,
            accion='actualizar_cliente',
            modelo='Cliente',
            descripcion=f'Cliente {cliente.rut} actualizado',
            objeto_id=cliente.id,
            datos_previos=datos_previos,
            datos_nuevos=response.data
        )

        return response

    def partial_update(self, request, *args, **kwargs):

        cliente = self.get_object()

        datos_previos = ClienteSerializer(
            cliente
        ).data

        response = super().partial_update(request, *args, **kwargs)

        registrar_auditoria(
            usuario=request.user,
            accion='actualizar_cliente',
            modelo='Cliente',
            descripcion=f'Cliente {cliente.rut} actualizado',
            objeto_id=cliente.id,
            datos_previos=datos_previos,
            datos_nuevos=response.data
        )

        return response

    def retrieve(self, request, *args, **kwargs):
        """Devuelve detalle de un cliente junto con estadisticas"""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #get_object() obtiene el cliente usando lookup_field='rut'
        cliente = self.get_object()

        #all() trae todos los vehiculos asociados
        vehiculos = cliente.vehiculos.all()

        #count() cuenta registros
        ordenes = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente
        )

        total_ordenes = ordenes.count()

        ordenes_activas = ordenes.filter(
            estado__in=[
                'Pendiente',
                'En progreso'
            ]
        ).count()

        #aggregate + Sum calcula dinero total gastado
        monto_total = ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "cliente": ClienteSerializer(
                cliente
            ).data,

            "vehiculos": VehiculoSerializer(
                vehiculos,
                many=True
            ).data,

            "stats": {

                "total_vehiculos": vehiculos.count(),
                "total_ordenes": total_ordenes,
                "ordenes_activas": ordenes_activas,
                "monto_total_gastado": monto_total
            }

        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Ordenes de un cliente",
        description="Devuelve todas las ordenes de los vehiculos de un cliente.",
        responses={200: OrdenTrabajoSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='ordenes')
    def ordenes(self, request, rut=None):
        """devolvera todas las ordenes asciadas a un vehiculo"""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #obtiene el cliente usando lookup_field='rut'
        cliente = self.get_object()

        #busca órdenes relacionadas al cliente
        #vehiculo__cliente navega entre relaciones FK
        ordenes = OrdenTrabajo.objects.select_related(
            'vehiculo',
            'mecanico'
        ).filter(
            vehiculo__cliente=cliente
        )

        #filtro opcional por estado
        estado_param = request.query_params.get('estado')

        if estado_param:

            ordenes = ordenes.filter(
                estado=estado_param
            )

        serializer = OrdenTrabajoSerializer(
            ordenes,
            many=True
        )

        return Response({

            "cliente": cliente.nombre,
            "total_ordenes": ordenes.count(),
            "ordenes": serializer.data

        }, status=status.HTTP_200_OK)

class VehiculoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar vehiculos"""

    permission_classes = [IsAuthenticated]

    #lookup_field = campo usado en URL
    lookup_field = 'patente'

    def get_serializer_class(self):

        #usa serializer especial para creacion
        if self.action == 'create':

            return VehiculoCreateSerializer

        return VehiculoSerializer

    def get_permissions(self):

        #solo admin puede modificar o eliminar vehiculos
        if self.action in [
            'update',
            'partial_update',
            'destroy'
        ]:

            return [EsAdministrador()]

        return [IsAuthenticated()]

    def get_queryset(self):
        """Obtiene vehículos aplicando filtros opcionales"""

        logger.debug(
            f"{self.request.method} {self.request.path} "
            f"params={self.request.query_params}"
        )

        #select_related optimiza relaciones FK
        vehiculos = Vehiculo.objects.select_related(
            'cliente'
        ).prefetch_related(
            'ordenes'
        )

        user = self.request.user

        #cliente solo ve sus vehiculos
        if es_cliente(user):

            vehiculos = vehiculos.filter(
                cliente__usuario=user
            )

        #mecanico solo ve vehiculos de sus ordenes
        elif es_mecanico(user):

            vehiculos = vehiculos.filter(
                ordenes__mecanico__usuario=user
            ).distinct()

        #filtro por marca
        marca = self.request.query_params.get('marca')

        if marca:

            vehiculos = vehiculos.filter(
                marca__iexact=marca
            )

        #filtro por rut cliente
        cliente_rut = self.request.query_params.get(
            'cliente_rut'
        )

        if cliente_rut:

            vehiculos = vehiculos.filter(
                cliente__rut=cliente_rut
            )

        #filtro por año desde
        anio_desde = self.request.query_params.get(
            'anio_desde'
        )

        if anio_desde:

            vehiculos = vehiculos.filter(
                anio__gte=anio_desde
            )

        #filtro año hasta
        anio_hasta = self.request.query_params.get(
            'anio_hasta'
        )

        if anio_hasta:

            vehiculos = vehiculos.filter(
                anio__lte=anio_hasta
            )

        return vehiculos

    def create(self, request, *args, **kwargs):

        #cliente solo puede crear vehiculos propios
        if es_cliente(request.user):

            cliente_id = request.data.get('cliente')

            if str(cliente_id) != str(request.user.cliente.id):

                return Response({
                    'error': 'Solo puedes crear vehículos a tu nombre'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        vehiculo = serializer.save()

        registrar_auditoria(
            usuario=request.user,
            accion='crear_vehiculo',
            modelo='Vehiculo',
            descripcion='Vehiculo creado',
            objeto_id=vehiculo.id,
            datos_nuevos=VehiculoSerializer(vehiculo).data
        )

        return Response(
            VehiculoSerializer(vehiculo).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        """Devuelve el detalle de un vehiculojunto con estadísticas de sus órdenes"""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #get_object() obtiene el vehiculo usando lookup_field='patente'
        vehiculo = self.get_object()

        # all() obtiene todas las ordenes relacionadas al vehículo
        ordenes = vehiculo.ordenes.all()

        #order_by ordena los registros yel signo "-" indica ordendescendente
        ultima_orden = ordenes.order_by(
            '-fecha_ingreso'
        ).first()

        ultima_visita = (
            ultima_orden.fecha_ingreso
            if ultima_orden
            else None
        )

        #aggregate + Sum suma montos en base de datos
        monto_total = ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "vehiculo": VehiculoSerializer(
                vehiculo
            ).data,

            "ordenes": OrdenTrabajoSerializer(
                ordenes,
                many=True
            ).data,

            "stats": {
                "total_ordenes": ordenes.count(),
                "ultima_visita": ultima_visita,
                "monto_total_gastado": monto_total
            }

        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Historial de vehiculo",
        description="Devuelve historial completo del vehiculo.",
        responses={200: OrdenTrabajoSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, patente=None):
        """Devuelve historial completo del vehículo."""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #obtiene vehículo usando lookup_field='patente'
        vehiculo = self.get_object()

        #select_related optimiza relaciones FK
        ordenes = vehiculo.ordenes.select_related(
            'mecanico'
        ).order_by(
            '-fecha_ingreso'
        )

        #aggregate realiza calculos Sql
        monto_total = ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        ultima_orden = ordenes.first()

        serializer = OrdenTrabajoSerializer(
            ordenes,
            many=True
        )

        return Response({

            "vehiculo": vehiculo.patente,
            "stats": {

                "total_visitas": ordenes.count(),
                "monto_total_gastado": monto_total,
                "ultimo_servicio": (
                    ultima_orden.fecha_ingreso
                    if ultima_orden
                    else None
                )
            },

            "ordenes": serializer.data

        }, status=status.HTTP_200_OK)

class OrdenViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar ordenes de trabajo"""

    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Serializer segun accion"""

        if self.action == 'create':
            return OrdenTrabajoCreateSerializer

        if self.action in ['update', 'partial_update']:
            return OrdenTrabajoUpdateSerializer

        return OrdenTrabajoSerializer

    def get_permissions(self):

        #solo admin o mecanico puede crear ordenes
        if self.action == 'create':

            return [EsAdministradorOMecanico()]

        #solo admin o mecanico puede modificar estado
        if self.action in [
            'update',
            'partial_update',
            'completar',
            'cancelar'
        ]:

            return [EsAdministradorOMecanico()]

        #solo admin puede eliminar ordenes
        if self.action == 'destroy':

            return [EsAdministrador()]

        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtrado por rol + filtros opcionales"""

        logger.debug(
            f"{self.request.method} {self.request.path} "
            f"params={self.request.query_params}"
        )

        ordenes = OrdenTrabajo.objects.select_related(
            'vehiculo__cliente',
            'mecanico'
        )

#filtros por rol
        user = self.request.user

        #acciones de modificacion no filtran para poder devolver 403
        if self.action not in [
            'update',
            'partial_update',
            'completar',
            'cancelar'
        ]:

            if es_cliente(user):

                ordenes = ordenes.filter(
                    vehiculo__cliente__usuario=user
                )

            elif es_mecanico(user):

                ordenes = ordenes.filter(
                    mecanico__usuario=user
                )

        estado_param = self.request.query_params.get('estado')

        if estado_param:

            ordenes = ordenes.filter(
                estado=estado_param
            )

        mecanico_rut = self.request.query_params.get('mecanico_rut')

        if mecanico_rut:

            ordenes = ordenes.filter(
                mecanico__rut=mecanico_rut
            )

        vehiculo_patente = self.request.query_params.get(
            'vehiculo_patente'
        )

        if vehiculo_patente:

            ordenes = ordenes.filter(
                vehiculo__patente__iexact=vehiculo_patente
            )

        vencidas = self.request.query_params.get('vencidas')

        if vencidas == 'true':

            ordenes = ordenes.filter(
                fecha_entrega_estimada__lt=timezone.now().date()
            ).exclude(
                estado__in=[
                    'Completada',
                    'Cancelada'
                ]
            )

        return ordenes

    def get_object(self):

        orden = super().get_object()

        user = self.request.user

        #valida que mecanico solo modifique sus ordenes
        if self.action in [
            'update',
            'partial_update',
            'completar',
            'cancelar'
        ]:

            if (
                es_mecanico(user)
                and
                orden.mecanico.usuario == user
            ):

                raise PermissionDenied(
                    'Solo puedes modificar tus propias órdenes'
                )

        return orden

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        orden = serializer.save()

        registrar_auditoria(
            usuario=request.user,
            accion='crear_orden',
            modelo='OrdenTrabajo',
            descripcion='Orden de trabajo creada',
            objeto_id=orden.id,
            datos_nuevos=OrdenTrabajoSerializer(orden).data
        )

        return Response(
            OrdenTrabajoSerializer(orden).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):

        orden = self.get_object()

        serializer = self.get_serializer(
            orden
        )

        return Response({
            "orden": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Completar una orden de trabajo",
        description="Marca la orden como Completada y registra el monto final.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'monto': {
                        'type': 'number'
                    },
                    'fecha_entrega_real': {
                        'type': 'string',
                        'format': 'date'
                    }
                },
                'required': [
                    'monto'
                ]
            }
        },
        responses={200: OrdenTrabajoSerializer}
    )
    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None):

        orden = self.get_object()

        if orden.estado == 'Completada':
            return Response({
                "error": "La orden ya estaba completada"
            }, status=status.HTTP_400_BAD_REQUEST)

        datos_previos = {
            'estado': orden.estado,
            'monto': str(orden.monto) if orden.monto else None,
            'fecha_entrega_real': (
                str(orden.fecha_entrega_real)
                if orden.fecha_entrega_real
                else None
            )
        }

        orden.estado = 'Completada'
        orden.monto = request.data.get('monto')
        orden.fecha_entrega_real = request.data.get(
            'fecha_entrega_real'
        )
        orden.save()

        registrar_auditoria(
            usuario=request.user,
            accion='completar_orden',
            modelo='OrdenTrabajo',
            descripcion=f'Orden {orden.id} completada',
            objeto_id=orden.id,
            datos_previos={
                'estado': orden.estado,
                'monto': str(orden.monto),
                'fecha_entrega_real': (
                    str(orden.fecha_entrega_real)
                    if orden.fecha_entrega_real
                    else None
                )
            },
            datos_nuevos=datos_previos,
        )

        return Response({
            "mensaje": "Orden completada correctamente",
            "orden": OrdenTrabajoSerializer(orden).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancelar una orden de trabajo",
        description="Marca la orden como Cancelada y guarda el motivo en observaciones.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'motivo': {
                        'type': 'string'
                    }
                }
            }
        },
        responses={200: OrdenTrabajoSerializer}
    )
    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):

        orden = self.get_object()

        datos_previos = {
            'estado': orden.estado,
            'observaciones': orden.observaciones
        }

        if orden.estado == 'Cancelada':
            return Response({
                "error": "La orden ya estaba cancelada"
            }, status=status.HTTP_400_BAD_REQUEST)

        orden.estado = 'Cancelada'
        orden.observaciones = request.data.get(
            'motivo',
            'Sin motivo'
        )
        orden.save()

        registrar_auditoria(
            usuario=request.user,
            accion='cancelar_orden',
            modelo='OrdenTrabajo',
            descripcion=f'Orden {orden.id} cancelada',
            objeto_id=orden.id,
            datos_previos=datos_previos,
            datos_nuevos={
                'estado': orden.estado,
                'observaciones': orden.observaciones
            }
        )

        return Response({
            "mensaje": "Orden cancelada correctamente",
            "orden": OrdenTrabajoSerializer(orden).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Resumen de ordenes",
        description="Devuelve metricas generales de ordenes y top 3 mecanicos.",
        responses={200: dict}
    )
    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):

        pendientes = OrdenTrabajo.objects.filter(estado='Pendiente').count()
        en_progreso = OrdenTrabajo.objects.filter(estado='En progreso').count()
        completadas = OrdenTrabajo.objects.filter(estado='Completada').count()
        canceladas = OrdenTrabajo.objects.filter(estado='Cancelada').count()

        monto_facturado = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).aggregate(total=Sum('monto'))['total'] or 0

        top_mecanicos = Mecanico.objects.annotate(
            total_ordenes=Count('ordenes')
        ).order_by('-total_ordenes')[:3]

        return Response({
            "resumen": {
                "pendientes": pendientes,
                "en_progreso": en_progreso,
                "completadas": completadas,
                "canceladas": canceladas,
                "monto_total_facturado": monto_facturado
            },
            "top_mecanicos": [
                {
                    "nombre": m.nombre,
                    "rut": m.rut,
                    "total_ordenes": m.total_ordenes
                }
                for m in top_mecanicos
            ]
        }, status=status.HTTP_200_OK)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet solo lectura para auditoria sistema"""

    #solo los administradores podran revisar logs
    permission_classes = [EsAdministrador]

    #serializer convierte logs a json
    serializer_class = AuditLogSerializer

    def get_queryset(self):

        #queryset ordena logs recientes primeroa
        logs = AuditLog.objects.select_related(
            'usuario'
        ).all()

        usuario = self.request.query_params.get('usuario')

        if usuario:

            logs = logs.filter(
                usuario__username=usuario
            )

        accion = self.request.query_params.get('accion')

        if accion:

            logs = logs.filter(
                accion=accion
            )

        modelo = self.request.query_params.get('modelo')

        if modelo:

            logs = logs.filter(
                modelo=modelo
            )

        desde = self.request.query_params.get('desde')

        if desde:

            logs = logs.filter(
                timestamp__gte=desde
            )

        hasta = self.request.query_params.get('hasta')

        if hasta:

            logs = logs.filter(
                timestamp__lte=hasta
            )

        return logs


class MeView(APIView):
    """Endpoint para obtener informacion usuario autenticado"""

    #solo usuarios autenticados pueden acceder endpoint
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Usuario autenticado",
        description="Devuelve datos basicos del usuario autenticado y su rol.",
        responses={200: dict}
    )
    def get(self, request):

        #user, usuario autenticado actual en jwt
        user = request.user

        rol = 'admin' if es_admin(user) else (
            'mecanico' if es_mecanico(user) else (
                'cliente' if es_cliente(user) else 'sin_rol'
            )
        )

        #data, respuesta json enviada al frontend
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'rol': rol
        }

        if rol == 'mecanico' and hasattr(user, 'mecanico'):

            data['mecanico'] = MecanicoSerializer(
                user.mecanico
            ).data

        elif rol == 'cliente' and hasattr(user, 'cliente'):

            data['cliente'] = ClienteResumenSerializer(
                user.cliente
            ).data

        return Response(
            data,
            status=status.HTTP_200_OK
        )


class RepuestoOrdenViewSet(viewsets.ModelViewSet):
    """
    Gestiona repuestos asociados a órdenes de trabajo.
    - Solo administrador puede crear, editar y eliminar.
    - Administrador y mecánico pueden ver.
    """

    #serializer encargado de validar y convertir repuestos a json
    serializer_class = RepuestoOrdenSerializer

    def get_queryset(self):

        #select_related trae la orden junto con el repuesto
        qs = RepuestoOrden.objects.select_related(
            'orden'
        )

        orden_id = self.request.query_params.get(
            'orden_id'
        )

        #permite filtrar repuestos por orden
        if orden_id:

            qs = qs.filter(
                orden_id=orden_id
            )

        return qs.order_by(
            'id'
        )

    def get_permissions(self):

        #solo admin puede crear, editar o eliminar repuestos
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy'
        ]:

            return [EsAdministrador()]

        #admin y mecanico pueden consultar repuestos
        return [EsAdministradorOMecanico()]
