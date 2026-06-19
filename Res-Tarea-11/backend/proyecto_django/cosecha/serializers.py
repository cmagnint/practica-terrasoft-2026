from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Supervisor,
    Trabajador,
    Cuartel,
    RegistroCosecha,
    AuditLog,
)

#serializer resumido para mostrar trabajadores anidados
class TrabajadorResumenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Trabajador
        fields = [
            'id',
            'nombre',
            'rut'
        ]


#serializer principal de supervisor
class SupervisorSerializer(serializers.ModelSerializer):

    #cantidad total de trabajadores asociados
    total_trabajadores = serializers.SerializerMethodField()

    #cantidad total de cuarteles asociados
    total_cuarteles = serializers.SerializerMethodField()

    class Meta:
        model = Supervisor
        fields = [
            'id',
            'nombre',
            'rut',
            'zona',
            'activo',
            'usuario',
            'total_trabajadores',
            'total_cuarteles'
        ]

    #retorna la cantidad de trabajadores del supervisor
    def get_total_trabajadores(self, obj):
        return obj.trabajadores.count()

    #retorna la cantidad de cuarteles del supervisor
    def get_total_cuarteles(self, obj):
        return obj.cuarteles.count()

#serializer principal de trabajador
class TrabajadorSerializer(serializers.ModelSerializer):

    #supervisor mostrado de forma anidada
    supervisor = SupervisorSerializer(read_only=True)

    class Meta:
        model = Trabajador
        fields = [
            'id',
            'nombre',
            'rut',
            'fecha_ingreso',
            'activo',
            'supervisor',
            'usuario'
        ]


#serializer principal de cuartel
class CuartelSerializer(serializers.ModelSerializer):

    #suma total de kilos registrados en el cuartel
    kilos_acumulados = serializers.SerializerMethodField()

    class Meta:
        model = Cuartel
        fields = [
            'id',
            'nombre',
            'hectareas',
            'variedad',
            'activo',
            'supervisor',
            'kilos_acumulados'
        ]

    #obtiene la suma total de kilos del cuartel
    def get_kilos_acumulados(self, obj):

        resultado = obj.registros.aggregate(
            total_kilos=Sum('kilos')
        )

        return resultado['total_kilos'] or 0

#serializer de lectura para registros de cosecha
class RegistroCosechaSerializer(serializers.ModelSerializer):

    #trabajador mostrado de forma anidada
    trabajador = TrabajadorResumenSerializer(read_only=True)

    #cuartel mostrado como texto legible
    cuartel = serializers.StringRelatedField()

    #calculo de kilos por hora
    rendimiento = serializers.SerializerMethodField()

    class Meta:
        model = RegistroCosecha
        fields = [
            'id',
            'trabajador',
            'cuartel',
            'fecha',
            'kilos',
            'horas',
            'calidad',
            'observaciones',
            'creado_en',
            'rendimiento'
        ]

    #calcula el rendimiento del registro
    def get_rendimiento(self, obj):
        return round(float(obj.kilos / obj.horas), 2)

#serializer utilizado para crear y editar registros
class RegistroCosechaCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegistroCosecha
        fields = [
            'trabajador',
            'cuartel',
            'fecha',
            'kilos',
            'horas',
            'calidad',
            'observaciones'
        ]

    #validaciones de negocio
    def validate(self, data):

        trabajador = data.get('trabajador') or self.instance.trabajador
        cuartel = data.get('cuartel') or self.instance.cuartel

        kilos = data.get('kilos') or self.instance.kilos
        horas = data.get('horas') or self.instance.horas
        calidad = data.get('calidad') or self.instance.calidad

        #valida kilos positivos
        if kilos < 0:
            raise serializers.ValidationError({
                'kilos': 'Los kilos no pueden ser negativos'
            })

        #valida horas dentro del rango permitido
        if horas <= 0 or horas > 12:
            raise serializers.ValidationError({
                'horas': 'Las horas deben estar entre 0 y 12'
            })

        #valida descarte con kilos cero
        if calidad == 'Descarte' and kilos == 0:
            raise serializers.ValidationError({
                'kilos': 'Un registro de descarte debe tener kilos mayores a cero'
            })

        #valida que trabajador y cuartel pertenezcan al mismo supervisor
        if trabajador.supervisor_id != cuartel.supervisor_id:
            raise serializers.ValidationError({
                'cuartel': (
                    'El cuartel no pertenece a la cuadrilla del trabajador'
                )
            })

        return data

#serializer para visualizar las auditorias
class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog

        fields = [
           'id',
            'usuario',
            'accion',
            'modelo',
            'objeto_id',
            'descripcion',
            'datos_previos',
            'datos_nuevos',
            'timestamp'
        ]