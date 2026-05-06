from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Min, Max
from django.db import IntegrityError
import logging

from .models import Temporero, Cuartel, Labor
from .serializers import (
    TemporeroSerializer,
    CuartelSerializer,
    LaborSerializer,
    LaborCreateSerializer,
)

#logger configurado en settings.py
logger = logging.getLogger('temporeros')


class TemporeroListView(APIView):
    """GET /api/temporeros/ - Lista temporeros con filtros opcionales."""

    def get(self, request):
        #log para ver la request en consola
        logger.debug(f"GET {request.path} — params: {request.query_params}")

        temporeros = Temporero.objects.all()

        #filtro por activo: ?activo=true o ?activo=false
        activo = request.query_params.get('activo')
        if activo is not None:
            temporeros = temporeros.filter(activo=activo.lower() == 'true')

        #filtro por supervisor: ?supervisor=true
        supervisor = request.query_params.get('supervisor')
        if supervisor is not None:
            temporeros = temporeros.filter(supervisor=supervisor.lower() == 'true')

        #filtro por talla: ?talla=XL
        talla = request.query_params.get('talla')
        if talla:
            temporeros = temporeros.filter(talla_polera=talla)

        #busqueda por nombre: ?buscar=juan
        buscar = request.query_params.get('buscar')
        if buscar:
            temporeros = temporeros.filter(nombre__icontains=buscar)

        #convierte objetos Django a JSON
        serializer = TemporeroSerializer(temporeros, many=True)

        return Response({
            "total": temporeros.count(),
            "temporeros": serializer.data
        }, status=status.HTTP_200_OK)


class TemporeroDetailView(APIView):
    """GET /api/temporeros/<rut>/ - Devuelve detalle de un temporero."""

    def get(self, request, rut):
        logger.debug(f"GET {request.path}")

        try:
            #busca el temporero por RUT
            temporero = Temporero.objects.get(rut=rut)
        except Temporero.DoesNotExist:
            #si no existe, responde error 404 en JSON
            return Response({
                "error": f"Temporero con RUT '{rut}' no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)

        #serializa un solo objeto
        serializer = TemporeroSerializer(temporero)

        return Response({
            "temporero": serializer.data
        }, status=status.HTTP_200_OK)


class CuartelListView(APIView):
    """GET /api/cuarteles/ - Lista cuarteles con filtros opcionales."""

    def get(self, request):
        #log para revisar filtros enviados desde navegador/frontend
        logger.debug(f"GET {request.path} — params: {request.query_params}")

        cuarteles = Cuartel.objects.all()

        #filtro por activo: ?activo=true o ?activo=false
        activo = request.query_params.get('activo')
        if activo is not None:
            cuarteles = cuarteles.filter(activo=activo.lower() == 'true')

        #filtro por variedad: ?variedad=Legacy
        variedad = request.query_params.get('variedad')
        if variedad:
            cuarteles = cuarteles.filter(variedad=variedad)

        #convierte queryset de cuarteles a JSON
        serializer = CuartelSerializer(cuarteles, many=True)

        return Response({
            "total": cuarteles.count(),
            "cuarteles": serializer.data
        }, status=status.HTTP_200_OK)

class CuartelDetailView(APIView):
    """GET /api/cuarteles/<nombre>/ - Detalle y métricas del cuartel."""

    def get(self, request, nombre):

        logger.debug(f"GET {request.path}")

        try:
            #buscara cuartel por nombre
            cuartel = Cuartel.objects.get(nombre__iexact=nombre) 
            #iexact ignora mayus y minus, ahora se puede buscar cuartel A-1 y a-1 por igual
        except Cuartel.DoesNotExist:

            return Response({
                "error": f"Cuartel '{nombre}' no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)

        #serializa información básica
        serializer = CuartelSerializer(cuartel)

        #todas las labores del cuartel
        labores = cuartel.labores.all()

        #aggregate() calcula métricas directo en SQL
        productividad = labores.aggregate(

            #SUM(kilos_cosechados)
            total_kilos_cosechados=Sum('kilos_cosechados'),

            #SUM(horas_trabajadas)
            total_horas_trabajadas=Sum('horas_trabajadas'),
            # Si SUM devuelve None, lo convertimos a 0

            #COUNT(id)
            cantidad_cosechas=Count('id'),

            #COUNT DISTINCT temporero
            temporeros_distintos=Count('temporero', distinct=True),
        )

        productividad['total_kilos_cosechados'] = (
            productividad['total_kilos_cosechados'] or 0
        )

        productividad['total_horas_trabajadas'] = (
            productividad['total_horas_trabajadas'] or 0
        )

        #evitamos la división por cero
        total_kilos = productividad['total_kilos_cosechados'] or 0

        productividad['kg_por_hectarea'] = (
            total_kilos / cuartel.hectareas
            if cuartel.hectareas > 0 else 0
        )

        #cuenta labores agrupadas por tipo
        labores_por_tipo = {}

        tipos = (
            labores
            .values('tipo')
            .annotate(total=Count('id'))
        )

        for item in tipos:
            labores_por_tipo[item['tipo']] = item['total']

        return Response({

            "cuartel": serializer.data,

            "productividad": productividad,

            "labores_por_tipo": labores_por_tipo

        }, status=status.HTTP_200_OK)


class LaborView(APIView):
    """
    GET  /api/labores/
    POST /api/labores/
    """

    def get(self, request):

        logger.debug(f"GET {request.path} — params: {request.query_params}")

        labores = Labor.objects.all()

        #filtro por tipo
        tipo = request.query_params.get('tipo')
        if tipo:
            labores = labores.filter(tipo=tipo)

        #filtro por cuartel con el iexact para buscar en min o mayus
        cuartel = request.query_params.get('cuartel')
        if cuartel:
            labores = labores.filter(cuartel__nombre__iexact=cuartel)

        #filtro por rut de temporero
        temporero_rut = request.query_params.get('temporero_rut')
        if temporero_rut:
            labores = labores.filter(
                temporero__rut=temporero_rut
            )

        #fecha desde
        desde = request.query_params.get('desde')
        if desde:
            labores = labores.filter(fecha__gte=desde)

        #fecha hasta
        hasta = request.query_params.get('hasta')
        if hasta:
            labores = labores.filter(fecha__lte=hasta)

        #limite de resultados, convierte el limite a numeros
        #en caso de que alguien mande algo invalido
        limite = request.query_params.get('limite', 100)

        try:
            limite = int(limite)
        except ValueError:
            limite = 100

        #maximo permitido, asi evitamos que pidan demasiados datos
        limite = min(limite, 500)

        total = labores.count()

        labores = labores[:limite]

        serializer = LaborSerializer(labores, many=True)

        respuesta = {
            "total": total,
            "mostrando": len(serializer.data),
            "labores": serializer.data
        }

        #mensaje si es qe hay más resultados
        if total > limite:
            respuesta["aviso"] = (
                f"mostrando {limite} de {total}"
            )

        return Response(
            respuesta,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        logger.debug(
            f"POST {request.path} — body: {request.data}"
        )

        #valida el JSON recibido
        serializer = LaborCreateSerializer(
            data=request.data
        )

        #si falla validación, envia 400
        if not serializer.is_valid():

            #detecta conflicto por UniqueConstraint
            if 'non_field_errors' in serializer.errors:

                return Response({
                    "error": (
                        "Ya existe una labor de este tipo "
                        "para este temporero en este cuartel y fecha"
                    )
                }, status=status.HTTP_409_CONFLICT)

            #otros errores de validación
            return Response({
            "errores": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            #guardar en la bdd
            labor = serializer.save()

            return Response({

                "mensaje": "Labor creada correctamente",

                "labor": LaborSerializer(labor).data

            }, status=status.HTTP_201_CREATED)

        except IntegrityError:

            return Response({

                "error": (
                    "Ya existe una labor con esos datos"
                )

            }, status=status.HTTP_409_CONFLICT)

class ResumenView(APIView):
    """GET /api/resumen/ - Entrega estadísticas generales del sistema."""

    def get(self, request):
        #log para registrar que se pidio en el resumen general
        logger.debug(f"GET {request.path}")

        #estadisticas simples de temporeros
        temporeros_data = {
            "activos": Temporero.objects.filter(activo=True).count(),
            "inactivos": Temporero.objects.filter(activo=False).count(),
            "supervisores": Temporero.objects.filter(supervisor=True).count(),
        }

        #aggregate() permite calcular totales directamente en la bdd
        cuarteles_agregados = Cuartel.objects.aggregate(
            total_hectareas=Sum('hectareas')
        )

        cuarteles_data = {
            "activos": Cuartel.objects.filter(activo=True).count(),
            "total_hectareas": cuarteles_agregados["total_hectareas"] or 0,
        }

        #datos generales de labores
        labores_agregadas = Labor.objects.aggregate(
            total_horas=Sum('horas_trabajadas'),
            total_kilos_cosechados=Sum('kilos_cosechados'),
            fecha_inicio=Min('fecha'),
            fecha_fin=Max('fecha'),
        )

        #se agrupan labores por tipo, segun entendi es el equivalente a usar group by
        labores_por_tipo_query = (
            Labor.objects
            .values('tipo')
            .annotate(total=Count('id'))
        )

        labores_por_tipo = {}

        #convertimos el resultado del ORM a diccionario JSON simple
        for item in labores_por_tipo_query:
            labores_por_tipo[item['tipo']] = item['total']

        labores_data = {
            "total": Labor.objects.count(),
            "fecha_inicio": labores_agregadas["fecha_inicio"],
            "fecha_fin": labores_agregadas["fecha_fin"],
            "total_horas": labores_agregadas["total_horas"] or 0,
            "total_kilos_cosechados": labores_agregadas["total_kilos_cosechados"] or 0,
            "por_tipo": labores_por_tipo,
        }

        return Response({
            "temporeros": temporeros_data,
            "cuarteles": cuarteles_data,
            "labores": labores_data,
        }, status=status.HTTP_200_OK)
