from datetime import date

from rest_framework import serializers  #base de Drf
from .models import Temporero, Cuartel, Labor


class TemporeroSerializer(serializers.ModelSerializer):
    """
    Serializer que convierte objetos Temporero a JSON
    también agrega el campo calculado 'edad'
    """

    #este campo no existe en la bdd, por lo tando se debe calcular asi
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Temporero  #modelo que se serializara

        #campos que se incluirán en la respuesta JSON
        fields = [
            'id',
            'nombre',
            'rut',
            'telefono',
            'contacto_emergencia',
            'fecha_ingreso',
            'supervisor',
            'fecha_nacimiento',
            'talla_polera',
            'activo',
            'edad',
        ]

    def get_edad(self, obj):
        """
        Calcula la edad a partir de la fecha de nacimiento.
        DRF llama automáticamente a este método.
        """

        #si no hay fecha, se evita el error
        if not obj.fecha_nacimiento:
            return None

        hoy = date.today()

        #calculo de edad
        return hoy.year - obj.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
        )

class CuartelSerializer(serializers.ModelSerializer):
    """ cuenta cuantas labores tiene el cuartel """

    cantidad_labores = serializers.SerializerMethodField() #campo que calcula usando related_name="labores"

    class Meta:
        model = Cuartel

        fields = [
            'id',
            'nombre',
            'hectareas',
            'variedad',
            'activo',
            'cantidad_labores',
        ]

    def get_cantidad_labores(self, obj):
        """ esto contara cuantas labores tiene el cuartel """

        return obj.labores.count()


class LaborSerializer(serializers.ModelSerializer):
    """ este serializer es para la lectura de labores, incluyen nombres legibles de FK """

    temporero_nombre = serializers.SerializerMethodField() #nombre del temporero
    cuartel_nombre = serializers.SerializerMethodField() #nombre del cuartel

    class Meta:
        model = Labor

        fields = [
            'id',
            'temporero',
            'temporero_nombre',
            'cuartel',
            'cuartel_nombre',
            'tipo',
            'fecha',
            'horas_trabajadas',
            'kilos_cosechados',
            'observaciones',
        ]

        #DRF (DjangoRestFramework) por defecto convierte decimal a string, pero esto fuerza numeros reales en JSON
        extra_kwargs = {
            'horas_trabajadas': {'coerce_to_string': False},
            'kilos_cosechados': {'coerce_to_string': False},
        }

    def get_temporero_nombre(self, obj): #obtiene el nombre del temporero relacionado

        return obj.temporero.nombre

    def get_cuartel_nombre(self, obj): #obtiene el nombre del cuartel relacionado

        return obj.cuartel.nombre

class LaborCreateSerializer(serializers.ModelSerializer): #este serializer crea labores via POST

    class Meta:
        model = Labor

        fields = [
            'temporero',
            'cuartel',
            'tipo',
            'fecha',
            'horas_trabajadas',
            'kilos_cosechados',
            'observaciones',
        ]

        extra_kwards = {
            'horas_trabajadas': {'coerce_to_string': False},
            'kilos_cosechados': {'coerce_to_string': False},
        }

    def validate(self, data):
        """ validaciones de negocio antes de guardar """

        tipo = data.get('tipo')
        kilos = data.get('kilos_cosechados')
        horas = data.get('horas_trabajadas')

        #las cosechas deben tener kilos
        if tipo == 'Cosecha' and kilos is None:
            raise serializers.ValidationError({
                'kilos_cosechados': 'obligatorio para tipo de cosecha'
            })
        #se encarga de que otros tipos no deban tener kilos, solo cosecha
        if tipo != 'Cosecha' and kilos is not None:
            raise serializers.ValidationError({
                'kilos_cosechados': 'solo aplica para tipos de cosecha'
            })
        #este campo valida las horas
        if horas <= 0 or horas > 12:
            raise serializers.ValidationError({
                'horas_trabajadas': 'debe estar entre 0 y 12'
            })

        return data
