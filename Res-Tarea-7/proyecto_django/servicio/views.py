# Create your views here.
import logging

from django.db.models import Sum, Avg, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

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
    OrdenTrabajoSerializer,
    OrdenTrabajoCreateSerializer,
    OrdenTrabajoUpdateSerializer
)

#logger propio de la app servicio
logger = logging.getLogger('servicio')

class MecanicoListView(APIView):
    """get y post de mecanicos"""

    def get(self, request):
        #log para registrar la request
        logger.debug(f"GET {request.path} params={request.query_params}")

        #query base
        mecanicos = Mecanico.objects.all()

        #filtro opcional por activo
        activo = request.query_params.get('activo')
        if activo is not None:
            mecanicos = mecanicos.filter(
                activo=activo.lower() == 'true'
            )

        #filtro opcional por especialidad
        especialidad = request.query_params.get('especialidad')
        if especialidad:
            mecanicos = mecanicos.filter(
                especialidad=especialidad
            )

        #serializa varios mecanicos
        serializer = MecanicoSerializer(
            mecanicos,
            many=True
        )

        return Response({
            "total": mecanicos.count(),
            "mecanicos": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        #log para ver el json recibido
        logger.debug(f"POST {request.path} body={request.data}")

        #antes de crear revisamos si el rut ya existe
        rut = request.data.get('rut')
        if rut and Mecanico.objects.filter(rut=rut).exists():
            return Response({
                "error": f"Ya existe un mecánico con el RUT '{rut}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        #usa el serializer normal para validar y crear
        serializer = MecanicoSerializer(
            data=request.data
        )

        if serializer.is_valid():
            mecanico = serializer.save()

            return Response({
                "mensaje": "Mecánico creado",
                "mecanico": MecanicoSerializer(mecanico).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "errores": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MecanicoDetailView(APIView):
    """detalle de mecanico por rut"""

    def get(self, request, rut):
        logger.debug(f"GET {request.path}")

        try:
            #busca mecanico por rut
            mecanico = Mecanico.objects.get(rut=rut)

        except Mecanico.DoesNotExist:
            return Response({
                "error": f"Mecánico con RUT '{rut}' no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)

        #ordenes activas son pendientes o en progreso
        ordenes_activas = (
            mecanico.ordenes
            .select_related('vehiculo', 'mecanico')
            .filter(estado__in=['Pendiente', 'En progreso'])
        )

        #estadisticas del mecanico
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
            "mecanico": MecanicoSerializer(mecanico).data,
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

class ClienteListView(APIView):
    """lista clientes"""

    def get(self, request):

        logger.debug(f"GET {request.path}")

        #prefetch_related optimiza relacion uno a muchos
        clientes = Cliente.objects.prefetch_related(
            'vehiculos'
        )

        serializer = ClienteSerializer(
            clientes,
            many=True
        )

        return Response({
            "total": clientes.count(),
            "clientes": serializer.data
        })


class ClienteDetailView(APIView):
    """detalle cliente por rut"""

    def get(self, request, rut):

        logger.debug(f"GET {request.path}")

        try:

            #trae vehiculos relacionados en menos consultas
            cliente = Cliente.objects.prefetch_related(
                'vehiculos__ordenes'
            ).get(rut=rut)

        except Cliente.DoesNotExist:

            return Response({
                "error": f"Cliente con RUT '{rut}' no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)

        #obtiene todos los vehiculos del cliente
        vehiculos = cliente.vehiculos.all()

        #cuenta total de ordenes
        total_ordenes = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente
        ).count()

        #suma total facturado
        monto_total = OrdenTrabajo.objects.filter(
            vehiculo__cliente=cliente,
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({

            "cliente": ClienteSerializer(cliente).data,

            "stats": {

                "total_vehiculos": vehiculos.count(),

                "total_ordenes": total_ordenes,

                "monto_total_facturado": monto_total
            }
        })

class VehiculoListView(APIView):
    """lista vehiculos con filtros"""

    def get(self, request):

        logger.debug(f"GET {request.path} params={request.query_params}")

        #select_related trae el cliente junto con el vehiculo yprefetch_related trae las ordenes asociadas
        vehiculos = Vehiculo.objects.select_related(
            'cliente'
        ).prefetch_related(
            'ordenes'
        )

        #filtro por marca
        marca = request.query_params.get('marca')
        if marca:
            vehiculos = vehiculos.filter(
                marca__iexact=marca
            )

        #filtro por rut del cliente
        cliente_rut = request.query_params.get('cliente_rut')
        if cliente_rut:
            vehiculos = vehiculos.filter(
                cliente__rut=cliente_rut
            )

        #filtro por año desde
        anio_desde = request.query_params.get('anio_desde')
        if anio_desde:
            vehiculos = vehiculos.filter(
                anio__gte=anio_desde
            )

        #filtro por año hasta
        anio_hasta = request.query_params.get('anio_hasta')
        if anio_hasta:
            vehiculos = vehiculos.filter(
                anio__lte=anio_hasta
            )

        serializer = VehiculoSerializer(
            vehiculos,
            many=True
        )

        return Response({
            "total": vehiculos.count(),
            "vehiculos": serializer.data
        }, status=status.HTTP_200_OK)


class VehiculoDetailView(APIView):
    """detalle de vehiculo por patente"""

    def get(self, request, patente):

        logger.debug(f"GET {request.path}")

        try:
            #busca por patente ignorando mayusculas y minusculas
            vehiculo = Vehiculo.objects.select_related(
                'cliente'
            ).prefetch_related(
                'ordenes'
            ).get(
                patente__iexact=patente
            )

        except Vehiculo.DoesNotExist:

            return Response({
                "error": f"Vehículo con patente '{patente}' no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)

        #ordenes del vehiculo
        ordenes = vehiculo.ordenes.all()

        #ultima visita segun fecha de ingreso mas reciente
        ultima_orden = ordenes.order_by(
            '-fecha_ingreso'
        ).first()

        ultima_visita = (
            ultima_orden.fecha_ingreso
            if ultima_orden
            else None
        )

        #suma montos de ordenes completadas
        monto_total = ordenes.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0

        return Response({
            "vehiculo": VehiculoSerializer(vehiculo).data,
            "stats": {
                "total_ordenes": ordenes.count(),
                "ultima_visita": ultima_visita,
                "monto_total_gastado": monto_total
            }
        }, status=status.HTTP_200_OK)

class OrdenTrabajoListCreateView(APIView):
    """lista y crea ordenes de trabajo"""

    def get(self, request):
        #este endpoint permite listar ordenes y aplicar filtros por query params
        logger.debug(f"GET {request.path} params={request.query_params}")

        #select_related es importante porque OrdenTrabajo tiene foreign keys a Vehiculo y Mecanico
        #vehiculo__cliente permite traer tambien al cliente dueño del vehiculo, evitando consultas de mas a la bdd
        ordenes = OrdenTrabajo.objects.select_related(
            'vehiculo__cliente',
            'mecanico'
        )

        #filtro por estado
        estado = request.query_params.get('estado')
        if estado:
            ordenes = ordenes.filter(
                estado=estado
            )

        #filtro por rut del mecanico
        mecanico_rut = request.query_params.get('mecanico_rut')
        if mecanico_rut:
            ordenes = ordenes.filter(
                mecanico__rut=mecanico_rut
            )

        #filtro por patente del vehiculo
        vehiculo_patente = request.query_params.get('vehiculo_patente')
        if vehiculo_patente:
            ordenes = ordenes.filter(
                vehiculo__patente__iexact=vehiculo_patente
            )

        #filtro para ordenes vencidas, aquellas que la fecha estimada ya paso y que aun no esta completada ni cancelada
        vencidas = request.query_params.get('vencidas')
        if vencidas == 'true':
            ordenes = ordenes.filter(
                fecha_entrega_estimada__lt=timezone.now().date()
            ).exclude(
                estado__in=['Completada', 'Cancelada']
            )

        #serializa muchas ordenes
        serializer = OrdenTrabajoSerializer(
            ordenes,
            many=True
        )

        return Response({
            "total": ordenes.count(),
            "ordenes": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        #este endpoint crea una orden nueva, para crear se usa un serializer distinto al de lectura, porque aqui se reciben ids, no objetos anidados
        logger.debug(f"POST {request.path} body={request.data}")

        serializer = OrdenTrabajoCreateSerializer(
            data=request.data
        )

        #is_valid revisa que existan vehiculo, mecanico y datos que sean obligatorios
        if not serializer.is_valid():
            return Response({
                "errores": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        #save crea la orden en la base de datos
        orden = serializer.save()

        #para responder usamos el serializer completo, asi el cliente recibe vehiculo y mecanico anidados
        return Response({
            "mensaje": "Orden creada",
            "orden": OrdenTrabajoSerializer(orden).data
        }, status=status.HTTP_201_CREATED)


class OrdenTrabajoDetailView(APIView):
    """detalle y actualizacion parcial de orden"""

    def get_object(self, pk):
        #metodo auxiliar para no repetir la misma consulta en get y patch
        #select_related trae las relaciones principales en una sola consulta
        return OrdenTrabajo.objects.select_related(
            'vehiculo__cliente',
            'mecanico'
        ).get(pk=pk)

    def get(self, request, pk):
        #detalle de una orden especifica por id
        logger.debug(f"GET {request.path}")

        try:
            orden = self.get_object(pk)

        except OrdenTrabajo.DoesNotExist:
            return Response({
                "error": f"Orden con id '{pk}' no encontrada"
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "orden": OrdenTrabajoSerializer(orden).data
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        #patch permite actualizar solo algunos campos
        #por ejemplo cambiar estado, monto o fecha de entrega real
        logger.debug(f"PATCH {request.path} body={request.data}")

        try:
            orden = self.get_object(pk)

        except OrdenTrabajo.DoesNotExist:
            return Response({
                "error": f"Orden con id '{pk}' no encontrada"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = OrdenTrabajoUpdateSerializer(
            orden,
            data=request.data,
            partial=True
        )

        #aqui se ejecuta la validacion del serializer
        #por ejemplo: si estado es Completada, monto es obligatorio
        if not serializer.is_valid():
            return Response({
                "errores": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        #guarda los cambios en la bdd
        orden_actualizada = serializer.save()

        #responde con la orden completa y anidada
        return Response({
            "mensaje": "Orden actualizada",
            "orden": OrdenTrabajoSerializer(orden_actualizada).data
        }, status=status.HTTP_200_OK)

class EstadisticasView(APIView):
    """estadisticas generales del taller"""

    def get(self, request):

        #log de la request
        logger.debug(f"GET {request.path}")

        #count cuenta registros directamente en la bdd
        total_clientes = Cliente.objects.count()

        total_vehiculos = Vehiculo.objects.count()

        total_ordenes = OrdenTrabajo.objects.count()


        #cuenta ordenes segun estado
        ordenes_pendientes = OrdenTrabajo.objects.filter(
            estado='Pendiente'
        ).count()

        ordenes_en_progreso = OrdenTrabajo.objects.filter(
            estado='En progreso'
        ).count()

        ordenes_completadas = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).count()

        ordenes_canceladas = OrdenTrabajo.objects.filter(
            estado='Cancelada'
        ).count()


        #aggregate permite calcular operaciones globales y sum suma todos los montos
        monto_total = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0


        #promedio de montos
        promedio_montos = OrdenTrabajo.objects.filter(
            estado='Completada'
        ).aggregate(
            promedio=Avg('monto')
        )['promedio'] or 0


        #annotate agrega campos calculados a cada mecanico y count cuenta cuantas ordenes tiene cada mecanico
        mecanico_top = Mecanico.objects.annotate(
            total_ordenes=Count('ordenes')
        ).order_by(
            '-total_ordenes'
        ).first()


        #si existe mecanico devuelve informacion resumida
        mecanico_con_mas_ordenes = None

        if mecanico_top:

            mecanico_con_mas_ordenes = {

                "nombre": mecanico_top.nombre,

                "rut": mecanico_top.rut,

                "total_ordenes": mecanico_top.total_ordenes
            }


        #respuesta final del endpoint
        return Response({

            "totales": {

                "clientes": total_clientes,

                "vehiculos": total_vehiculos,

                "ordenes": total_ordenes
            },

            "ordenes_por_estado": {

                "pendientes": ordenes_pendientes,

                "en_progreso": ordenes_en_progreso,

                "completadas": ordenes_completadas,

                "canceladas": ordenes_canceladas
            },

            "facturacion": {

                "monto_total": monto_total,

                #round redondea a 2 decimales
                "promedio_montos": round(
                    promedio_montos,
                    2
                )
            },

            "mecanico_con_mas_ordenes": (
                mecanico_con_mas_ordenes
            )

        }, status=status.HTTP_200_OK)
