import random
from datetime import timedelta

from django.core.management.base import BaseCommand

from django.utils import timezone

from servicio.models import (
    Mecanico,
    Cliente,
    Vehiculo,
    OrdenTrabajo
)


#clase principal del comando django
class Command(BaseCommand):

    #descripcion visible al ejecutar help
    help = 'puebla la base de datos con informacion de prueba'

    #metodo principal del comando
    def handle(self, *args, **kwargs):

        #elimina datos antiguos para evitar duplicados
        #el orden importa por las foreign key
        OrdenTrabajo.objects.all().delete()
        Vehiculo.objects.all().delete()
        Cliente.objects.all().delete()
        Mecanico.objects.all().delete()

        self.stdout.write(
            'datos antiguos eliminados'
        )


        #datos base de mecanicos
        #cada tupla contiene:
        #nombre
        #rut
        #especialidad
        #activo
        mecanicos_data = [

            ('Carlos Muñoz', '11111111-1', 'Motor', True),

            ('Ana López', '22222222-2', 'Electricidad', True),

            ('Pedro Soto', '33333333-3', 'Frenos', True),

            ('María Torres', '44444444-4', 'Carrocería', True),

            ('Luis Rojas', '55555555-5', 'General', True),

            ('Fernanda Díaz', '66666666-6', 'Motor', True),

            ('Jorge Silva', '77777777-7', 'Electricidad', True),

            ('Raúl Vega', '88888888-8', 'General', False),
        ]


        #creacion de mecanicos
        for nombre, rut, especialidad, activo in mecanicos_data:

            #create inserta un nuevo registro en la bd
            Mecanico.objects.create(

                nombre=nombre,

                rut=rut,

                especialidad=especialidad,

                activo=activo
            )

        self.stdout.write(
            'mecanicos creados'
        )


        #clientes de ejemplo
        clientes_data = [

            ('Juan Pérez', '10111111-1'),

            ('María González', '10222222-2'),

            ('Carlos Díaz', '10333333-3'),

            ('Ana Torres', '10444444-4'),

            ('Pedro Silva', '10555555-5'),

            ('Fernanda Soto', '10666666-6'),

            ('Luis Morales', '10777777-7'),

            ('Camila Rojas', '10888888-8'),

            ('Diego Herrera', '10999999-9'),

            ('Valentina Muñoz', '11000000-0'),

            ('Javiera Castro', '11122222-3'),

            ('Matías Fuentes', '11233333-4'),

            ('Constanza Reyes', '11344444-5'),

            ('Sebastián Araya', '11455555-6'),

            ('Daniela Peña', '11566666-7'),

            ('Francisco Leiva', '11677777-8'),

            ('Antonia Salazar', '11788888-9'),

            ('Ignacio Bravo', '11899999-0'),

            ('Paula Medina', '11911111-1'),

            ('Rodrigo Carrasco', '12022222-2'),
        ]


        #creacion de clientes
        for nombre, rut in clientes_data:

            Cliente.objects.create(

                nombre=nombre,

                rut=rut,

                telefono='912345678',

                #crea email automaticamente
                email=(
                    f'{nombre.lower().replace(" ", ".")}@mail.com'
                )
            )

        self.stdout.write(
            'clientes creados'
        )


        #diccionario de marcas y modelos reales
        vehiculos_data = {

            'Toyota': [
                'Corolla',
                'Yaris',
                'Hilux',
                'RAV4'
            ],

            'Hyundai': [
                'Accent',
                'Elantra',
                'Tucson',
                'Santa Fe'
            ],

            'Chevrolet': [
                'Sail',
                'Spark',
                'Tracker',
                'Groove'
            ],

            'Kia': [
                'Rio',
                'Cerato',
                'Sportage',
                'Morning'
            ],

            'Mazda': [
                'Mazda3',
                'CX-5',
                'BT-50',
                'CX-30'
            ]
        }


        #lista de colores disponibles
        colores = [

            'Blanco',

            'Negro',

            'Rojo',

            'Azul',

            'Gris',

            'Plata'
        ]


        #obtiene clientes desde la bd
        clientes = list(
            Cliente.objects.all()
        )


        #crea 35 vehiculos
        for i in range(35):

            #elige marca aleatoria
            marca = random.choice(
                list(vehiculos_data.keys())
            )

            #elige modelo perteneciente a esa marca
            modelo = random.choice(
                vehiculos_data[marca]
            )

            #distribuye vehiculos entre clientes
            cliente = clientes[
                i % len(clientes)
            ]

            Vehiculo.objects.create(

                #patente unica
                patente=f'ABCD{i:02}',

                marca=marca,

                modelo=modelo,

                #anio aleatorio
                anio=random.randint(
                    2014,
                    2024
                ),

                color=random.choice(colores),

                kilometraje=random.randint(
                    10000,
                    180000
                ),

                #foreign key hacia cliente
                cliente=cliente
            )

        self.stdout.write(
            'vehiculos creados'
        )


        #distribucion de estados
        estados = (

            ['Pendiente'] * 15 +

            ['En progreso'] * 10 +

            ['Completada'] * 30 +

            ['Cancelada'] * 5
        )


        #obtiene vehiculos y mecanicos
        vehiculos = list(
            Vehiculo.objects.all()
        )

        mecanicos = list(
            Mecanico.objects.all()
        )


        #fecha actual
        hoy = timezone.now().date()


        #crea 60 ordenes
        for i in range(60):

            estado = estados[i]

            #fecha estimada aleatoria
            fecha_estimada = (

                hoy +

                timedelta(
                    days=random.randint(1, 20)
                )
            )

            fecha_real = None

            monto = None


            #solo completadas tienen monto
            if estado == 'Completada':

                fecha_real = (

                    fecha_estimada +

                    timedelta(
                        days=random.randint(0, 5)
                    )
                )

                monto = random.randint(
                    50000,
                    500000
                )


            OrdenTrabajo.objects.create(

                #vehiculo aleatorio
                vehiculo=random.choice(
                    vehiculos
                ),

                #mecanico aleatorio
                mecanico=random.choice(
                    mecanicos
                ),

                descripcion=(
                    f'reparacion numero {i + 1}'
                ),

                estado=estado,

                fecha_entrega_estimada=fecha_estimada,

                fecha_entrega_real=fecha_real,

                monto=monto,

                observaciones=(
                    'orden generada automaticamente'
                )
            )

        self.stdout.write(

            self.style.SUCCESS(

                'base de datos poblada correctamente'
            )
        )
