from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import (Mecanico, Cliente, Vehiculo, OrdenTrabajo, AuditLog, RepuestoOrden)

class MecanicoSerializer(serializers.ModelSerializer):

    #campo calculado
    total_ordenes = serializers.SerializerMethodField()

    class Meta:
        model = Mecanico
        fields = '__all__'

    @extend_schema_field(serializers.IntegerField())
    #retorna cantidad total de ordenes del mecanico
    def get_total_ordenes(self, obj):
        return getattr(
            obj,
            'total_ordenes_anotado',
            obj.ordenes.count()
        )

class ClienteResumenSerializer(serializers.ModelSerializer):

    #serializer reducido para evitar referencias circulares
    class Meta:
        model = Cliente

        #campos minimos para mostrar cliente
        fields = [
            'id',
            'nombre',
            'rut',
            'telefono'
        ]


class VehiculoResumenSerializer(serializers.ModelSerializer):

    #serializer reducido para vehiculos
    class Meta:
        model = Vehiculo

        #campos principales del vehiculo
        fields = [
            'id',
            'patente',
            'marca',
            'modelo',
            'anio',
            'color'
        ]


class OrdenResumenSerializer(serializers.ModelSerializer):

    #serializer reducido para ordenes
    class Meta:
        model = OrdenTrabajo

        #campos resumidos de la orden
        fields = [
            'id',
            'estado',
            'fecha_ingreso',
            'fecha_entrega_estimada',
            'monto'
        ]


class ClienteSerializer(serializers.ModelSerializer):

    #nested serializer de vehiculos
    vehiculos = VehiculoResumenSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Cliente

        #incluye vehiculos asociados
        fields = [
            'id',
            'nombre',
            'rut',
            'telefono',
            'email',
            'fecha_registro',
            'vehiculos'
        ]


class VehiculoSerializer(serializers.ModelSerializer):

    #cliente anidado
    cliente = ClienteResumenSerializer(
        read_only=True
    )

    #ordenes asociadas al vehiculo
    ordenes = OrdenResumenSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Vehiculo
        fields = '__all__'


class VehiculoCreateSerializer(serializers.ModelSerializer):
    """serializer para crear vehiculos usando id de cliente"""

    class Meta:
        model = Vehiculo

        #aqui cliente recibe un id, no un objeto anidado
        fields = [
            'patente',
            'marca',
            'modelo',
            'anio',
            'color',
            'kilometraje',
            'cliente'
        ]


class OrdenTrabajoSerializer(serializers.ModelSerializer):

    #vehiculo anidado
    vehiculo = VehiculoResumenSerializer(
        read_only=True
    )

    #mecanico anidado
    mecanico = MecanicoSerializer(
        read_only=True
    )

    class Meta:
        model = OrdenTrabajo
        fields = '__all__'


class OrdenTrabajoCreateSerializer(serializers.ModelSerializer):

    #serializer para crear ordenes
    class Meta:
        model = OrdenTrabajo

        #solo ids y campos editables
        fields = [
            'vehiculo',
            'mecanico',
            'descripcion',
            'fecha_entrega_estimada',
            'observaciones'
        ]


class OrdenTrabajoUpdateSerializer(serializers.ModelSerializer):

    #serializer para actualizar ordenes
    class Meta:
        model = OrdenTrabajo

        #campos permitidos en patch
        fields = [
            'mecanico',
            'estado',
            'fecha_entrega_estimada',
            'fecha_entrega_real',
            'monto',
            'observaciones'
        ]

    #validaciones personalizadas
    def validate(self, data):

        estado = data.get('estado')
        monto = data.get('monto')

        #una orden completada debe tener monto
        if estado == "Completada" and monto is None:

            raise serializers.ValidationError({
                "monto": (
                    "obligatorio para marcar "
                    "una orden como completada"
                )
            })

        return data


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para mostrar registros de auditoria"""

    #usuario username, muestra nombre usuario en vez de solo id
    usuario_username = serializers.CharField(
        source='usuario.username',
        read_only=True
    )

    class Meta:

        #model indica que tabla usa este serializer
        model = AuditLog

        #fields define datos visibles en respuesta json
        fields = [
            'id',
            'usuario_username',
            'accion',
            'modelo',
            'objeto_id',
            'descripcion',
            'datos_previos',
            'datos_nuevos',
            'timestamp'
        ]

class RepuestoOrdenSerializer(serializers.ModelSerializer):
    """Serializer para repuestos asociados a ordenes"""

    class Meta:
        model = RepuestoOrden

        fields = [
            'id',
            'orden',
            'proveedor',
            'detalle',
            'costo_unitario',
            'cantidad',
            'costo_total',
            'archivo_origen',
            'fila_excel',
            'creado_en',
        ]

        #estos campos se calculan automaticamente
        read_only_fields = [
            'costo_total',
            'creado_en'
        ]

    def validate_costo_unitario(self, value):

        #el costo debe ser mayor a cero
        if value <= 0:

            raise serializers.ValidationError(
                "El costo unitario debe ser mayor a 0."
            )

        return value

    def validate_cantidad(self, value):

        #la cantidad debe ser mayor a cero
        if value <= 0:

            raise serializers.ValidationError(
                "La cantidad debe ser mayor a 0."
            )

        return value

    def validate_orden(self, value):

        #solo se aceptan repuestos para ordenes completadas
        if value.estado != 'Completada':

            raise serializers.ValidationError(
                "Solo se pueden registrar repuestos en ordenes Completadas."
            )

        return value

    def validate(self, attrs):

        archivo_origen = attrs.get(
            'archivo_origen'
        )

        fila_excel = attrs.get(
            'fila_excel'
        )

        #evita importar dos veces la misma fila del excel
        if archivo_origen and fila_excel:

            existe = RepuestoOrden.objects.filter(
                archivo_origen=archivo_origen,
                fila_excel=fila_excel
            ).exists()

            if existe:

                raise serializers.ValidationError(
                    "Esta fila del archivo ya fue importada anteriormente."
                )

        return attrs
