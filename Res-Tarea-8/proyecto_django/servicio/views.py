# Create your views here.
import logging

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date
from django.db.models import Sum, Avg, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .models import (
    Mecanico,
    Cliente,
    Vehiculo,
    OrdenTrabajo
)

from .serializers import (
    MecanicoSerializer,
    ClienteSerializer,
    VehiculoSerializer,
    VehiculoCreateSerializer,
    OrdenTrabajoSerializer,
    OrdenTrabajoCreateSerializer,
    OrdenTrabajoUpdateSerializer
)

#logger propio de la app servicio
logger = logging.getLogger('servicio')

"""MODIFICACIONES NUEVAS"""

class MecanicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar los mecanicos """

    #IsAuthenticated exige token válido JWT
    permission_classes = [IsAuthenticated]

    serializer_class = MecanicoSerializer
    queryset = Mecanico.objects.all()
    lookup_field = 'rut'

    def get_queryset(self):

        logger.debug(
            f"{self.request.method} {self.request.path}"
            f"params={self.request.query_params}"
        )

        mecanicos = Mecanico.objects.all()

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

    def list(self, reques, *args, **kwargs):
        """Lista de mecanicos con respuesta personalizada"""

        mecanicos = self.get_queryset()

        serializer = self.get_serializer(
            mecanicos,
            many=True
        )

        return Response ({
            "total": mecanicos.count(),
            "mecanicos": serializer.data
        }, status=status.HTTP_200_OK)

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
            estado='Cancelado'
        ).count()

        monto_total = mecanico.ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "mecanico":MecanicoSerializer(
                mecanico
            ).data,

            "ordenes activas": OrdenTrabajoSerializer(
                ordenes_activas,
                many=True
            ).data,

            "stats": {
                "ordenes_completadas": ordenes_completadas,
                "ordenes_canceladas": ordenes_canceladas,
                "monto_total_facturado": monto_total
            }

        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, rut=None):
        #action es como un endpoint personalizado dentro de un ViewSet
        #detail=True significa que trabaja sobre un mecanico específico

        mecanico = self.get_object()

        mecanico.activo = False
        mecanico.save()

        return Response({
            "mensaje": "Mecánico desactivado correctamente",
            "mecanico": MecanicoSerializer(mecanico).data
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        #detail=False significa que no usa un rut especifico

        mecanicos = Mecanico.objects.filter(
            activo=True
        )

        disponibles = []

        for mecanico in mecanicos:
            #count() cuenta cuantas ordenes activas tiene este mecanico
            ordenes_activas = mecanico.ordenes.filter(
                estado__in=[
                    'Pendiente',
                    'En progreso'
                ]
            ).count()

            if ordenes_activas < 3:
                disponibles.append(mecanico)
        serializer = MecanicoSerializer(
            disponibles,
            many=True
        )

        return Response({
            "total": len(disponibles),
            "mecanicos": serializer.data
        }, status=status.HTTP_200_OK)

"""MODIFICACIONES NUEVAS ARRIBA"""

#CODIGO ANTIGUO ELIMINADO: MecanicoListView y MecanicoDetailView

"""MODIFICACIONES NUEVAS ABAJO"""


class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet actualizado par gestionar clientes"""

    permission_classes = [IsAuthenticated]

    serializer_class = ClienteSerializer
    queryset = Cliente.objects.all()
    lookup_field = 'rut'

    def get_queryset(self):

        logger.debug(
            f"{self.request.method} {self.request.path} "
            f"params={self.request.query_params}"
        )

        clientes = Cliente.objects.prefetch_related( #patch_related optimiza relaciones MTM o reverse fk
            'vehiculos'
        )

        buscar = self.request.query_params.get('buscar')

        if buscar:
            clientes = clientes.filter(
                nombre_icontains=buscar
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

    def list(self, request, *args, **kwargs):

        clientes = self.get_queryset()

        serializer = self.get_serializer(
            clientes,
            many=True
        )

        return Response({
            "total": clientes.count(),
            "clientes": serializer.data
        }, status=status.HTTP_200_OK)

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
        total_ordenes = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente
        ).count()

        ordenes_activas = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente,
            estado__in=[
                'Pendiente',
                'En progreso'
            ]
        ).count()

        #aggregate + Sum calcula dinero total gastado
        monto_total = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente,
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "cliente": ClienteSerializer(
                cliente
            ).data,

            "stats": {

                "total_vehiculos": vehiculos.count(),
                "total_ordenes": total_ordenes,
                "ordenes_activas": ordenes_activas,
                "monto_total_gastado": monto_total
            }

        }, status=status.HTTP_200_OK)

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
        estado = request.query_params.get('estado')

        if estado:

            ordenes = ordenes.filter(
                estado=estado
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

"""BLOQUE ACTUALIZADO ARRIBA"""

#BLOQUES ANTIGUOS ELIMINADOS: ClienteListView(APIView) Y ClienteDetailView(APIView)

"""BLOQUE ACTUALIZADO ABAJO"""

class VehiculoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar vehiculos"""

    permission_classes = [IsAuthenticated]

    serializer_class = VehiculoSerializer
    queryset = Vehiculo.objects.all()

    #lookup_field = campo usado en URL
    lookup_field = 'patente'


    def get_queryset(self):
        """
        Obtiene vehículos aplicando filtros opcionales.
        """

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


    def list(self, request, *args, **kwargs):
        """Lista vehículos con formato personalizado."""

        vehiculos = self.get_queryset()

        serializer = self.get_serializer(
            vehiculos,
            many=True
        )

        return Response({

            "total": vehiculos.count(),
            "vehiculos": serializer.data

        }, status=status.HTTP_200_OK)

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

            "stats": {
                "total_ordenes": ordenes.count(),
                "ultima_visita": ultima_visita,
                "monto_total_gastado": monto_total
            }

        }, status=status.HTTP_200_OK)

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

"""BLOQUE ACTUALIZADO ARRIBA"""

#BLOQUES ANTIGUOS ELIMINADOS: VehiculoListView y VehiculoDetailView

"""BLOQUE A ACTUALIZAR ABAJO"""

class OrdenViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar órdenes de trabajo"""

    permission_classes = [IsAuthenticated]

    queryset = OrdenTrabajo.objects.all()
    #lookup_field define qu campo usa DRF en URLs
    #aquI usamos el id normal de la orden
    lookup_field = 'pk'


    def get_serializer_class(self):
        """Devuelve serializer según acción actual"""

        #self.action = acciOn actual del ViewSet
        #ejemplos: list, create, retrieve, update

        if self.action == 'create':

            return OrdenTrabajoCreateSerializer

        if self.action in [
            'update',
            'partial_update'
        ]:

            return OrdenTrabajoUpdateSerializer

        return OrdenTrabajoSerializer


    def get_queryset(self):
        """Obtiene órdenes aplicando filtros opcionales"""

        logger.debug(
            f"{self.request.method} {self.request.path} "
            f"params={self.request.query_params}"
        )

        #select_related optimiza relaciones FK
        ordenes = OrdenTrabajo.objects.select_related(
            'vehiculo__cliente',
            'mecanico'
        )

        #filtro por estado
        estado = self.request.query_params.get(
            'estado'
        )

        if estado:

            ordenes = ordenes.filter(
                estado=estado
            )

        #filtro por rut mecánico
        mecanico_rut = self.request.query_params.get(
            'mecanico_rut'
        )

        if mecanico_rut:

            ordenes = ordenes.filter(
                mecanico__rut=mecanico_rut
            )

        #filtro por patente vehiculo
        vehiculo_patente = self.request.query_params.get(
            'vehiculo_patente'
        )

        if vehiculo_patente:

            ordenes = ordenes.filter(
                vehiculo__patente__iexact=vehiculo_patente
            )

        #filtro órdenes vencidas
        vencidas = self.request.query_params.get(
            'vencidas'
        )

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

    def list(self, request, *args, **kwargs):
        """Lista órdenes con formato personalizado"""

        #get_queryset() aplica filtros dinamicos
        ordenes = self.get_queryset()

        serializer = self.get_serializer(
            ordenes,
            many=True
        )

        return Response({

            "total": ordenes.count(),

            "ordenes": serializer.data

        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Devuelve detalle de una orden"""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #get_object() obtiene la orden usando lookup_field='pk'
        orden = self.get_object()

        serializer = self.get_serializer(
            orden
        )

        return Response({

            "orden": serializer.data

        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None):
        """Marca una orden como completada"""

        logger.debug(
            f"{request.method} {request.path} "
            f"body={request.data}"
        )

        #obtiene orden usando pk
        orden = self.get_object()

        #validacin para evitar completar dos veces
        if orden.estado == 'Completada':

            return Response({
                "error": "La orden ya estaba completada"
            }, status=status.HTTP_400_BAD_REQUEST)

        #actualiza datos principales
        orden.estado = 'Completada'

        orden.monto = request.data.get(
            'monto'
        )

        orden.fecha_entrega_real = request.data.get(
            'fecha_entrega_real'
        )

        orden.save()

        serializer = OrdenTrabajoSerializer(
            orden
        )

        return Response({

            "mensaje": "Orden completada correctamente",

            "orden": serializer.data

        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """Cancela una orden de trabajo"""

        logger.debug(
            f"{request.method} {request.path} "
            f"body={request.data}"
        )

        #obtiene orden desde URL
        orden = self.get_object()

        #evita cancelar una orden ya cancelada
        if orden.estado == 'Cancelada':

            return Response({
                "error": "La orden ya estaba cancelada"
            }, status=status.HTTP_400_BAD_REQUEST)

        orden.estado = 'Cancelada'

        #obtiene motivo enviado en JSON
        motivo = request.data.get(
            'motivo',
            'Sin motivo especificado'
        )

        #guarda motivo en observaciones
        orden.observaciones = motivo

        orden.save()

        serializer = OrdenTrabajoSerializer(
            orden
        )

        return Response({

            "mensaje": "Orden cancelada correctamente",
            "orden": serializer.data

        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """Devuelve métricas generales de órdenes."""

        logger.debug(
            f"{request.method} {request.path}"
        )

        #count() cuenta registros
        pendientes = OrdenTrabajo.objects.filter(
            estado='Pendiente'
        ).count()

        en_progreso = OrdenTrabajo.objects.filter(
            estado='En progreso'
        ).count()

        completadas = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).count()

        canceladas = OrdenTrabajo.objects.filter(
            estado='Cancelada'
        ).count()

        #aggregate + Sum suma dinero facturado
        monto_facturado = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        #annotate agrega calculos extra a cada registro
        top_mecanicos = Mecanico.objects.annotate(

            #Count cuenta ordenes relacionadas
            total_ordenes=Count('ordenes')

        ).order_by(
            '-total_ordenes'
        )[:3]

        mecanicos_data = []

        for mecanico in top_mecanicos:

            mecanicos_data.append({

                "nombre": mecanico.nombre,
                "rut": mecanico.rut,
                "total_ordenes": mecanico.total_ordenes
            })

        return Response({

            "resumen": {

                "pendientes": pendientes,
                "en_progreso": en_progreso,
                "completadas": completadas,
                "canceladas": canceladas,
                "monto_total_facturado": monto_facturado
            },

            "top_mecanicos": mecanicos_data

        }, status=status.HTTP_200_OK)


"""BLOQUE ACTUALIZADO ARRIBA"""

#BLOQUE ANTIGUO ELIMINADOS:OrdenTrabajoListCreateView y OrdenTrabajoDetailView
