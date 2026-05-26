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


class Command(BaseCommand):
    help = 'puebla la base de datos con informacion de prueba'

    def handle(self, *args, **kwargs):
        #fecha actual segun django
        hoy = timezone.now().date()

        #(distribuir fechas en los ultimos 90 dias)
        dias_historicos = 90

        #datos base de mecanicos
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

        #crea mecanicos sin duplicar
        for nombre, rut, especialidad, activo in mecanicos_data:
            Mecanico.objects.get_or_create(
                rut=rut,
                defaults={
                    'nombre': nombre,
                    'especialidad': especialidad,
                    'activo': activo
                }
            )

        #datos base de clientes
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

        #crea clientes sin duplicar
        for nombre, rut in clientes_data:
            Cliente.objects.get_or_create(
                rut=rut,
                defaults={
                    'nombre': nombre,
                    'telefono': '912345678',
                    'email': f'{nombre.lower().replace(" ", ".")}@mail.com'
                }
            )

        #marcas y modelos coherentes
        vehiculos_data = {
            'Toyota': ['Corolla', 'Yaris', 'Hilux', 'RAV4'],
            'Hyundai': ['Accent', 'Elantra', 'Tucson', 'Santa Fe'],
            'Chevrolet': ['Sail', 'Spark', 'Tracker', 'Groove'],
            'Kia': ['Rio', 'Cerato', 'Sportage', 'Morning'],
            'Mazda': ['Mazda3', 'CX-5', 'BT-50', 'CX-30']
        }

        colores = [
            'Blanco',
            'Negro',
            'Rojo',
            'Azul',
            'Gris',
            'Plata'
        ]

        clientes = list(Cliente.objects.all())

        #crea 35 vehiculos sin duplicar
        for i in range(35):
            marca = random.choice(list(vehiculos_data.keys()))
            modelo = random.choice(vehiculos_data[marca])
            cliente = clientes[i % len(clientes)]

            Vehiculo.objects.get_or_create(
                patente=f'ABCD{i:02}',
                defaults={
                    'marca': marca,
                    'modelo': modelo,
                    'anio': random.randint(2014, 2024),
                    'color': random.choice(colores),
                    'kilometraje': random.randint(10000, 180000),
                    'cliente': cliente
                }
            )

        vehiculos = list(Vehiculo.objects.all())
        mecanicos = list(Mecanico.objects.all())

        estados = (
            ['Pendiente'] * 15 +
            ['En progreso'] * 10 +
            ['Completada'] * 30 +
            ['Cancelada'] * 5
        )

        #crea 60 ordenes sin duplicar
        for i, estado in enumerate(estados):
            vehiculo = vehiculos[i % len(vehiculos)]
            mecanico = mecanicos[i % len(mecanicos)]

            #fecha de ingreso historica p
            if estado in ['Pendiente', 'En progreso']:

                fecha_ingreso = hoy - timedelta(
                    days=random.randint(20, dias_historicos)
                )

            else:

                fecha_ingreso = hoy - timedelta(
                    days=random.randint(0, dias_historicos)
                )

            #fecha estimada posterior al ingreso, para ordenes activas antiguas, esta fecha quedara en el pasado
            fecha_estimada = fecha_ingreso + timedelta(
                days=random.randint(3, 15)
            )

            fecha_real = None
            monto = None

            #solo las ordenes completadas temdram fecha real y monto
            if estado == 'Completada':
                fecha_real = fecha_estimada + timedelta(
                    days=random.randint(0, 5)
                )

                monto = random.randint(30000, 500000)

            #si ya existe una orden con esta descripcion no crea otra
            OrdenTrabajo.objects.get_or_create(
                descripcion=f'reparacion numero {i + 1}',
                defaults={
                    'vehiculo': vehiculo,
                    'mecanico': mecanico,
                    'estado': estado,
                    'fecha_ingreso': fecha_ingreso,
                    'fecha_entrega_estimada': fecha_estimada,
                    'fecha_entrega_real': fecha_real,
                    'monto': monto,
                    'observaciones': 'orden generada automaticamente'
                }
            )
        #print final
        self.stdout.write('============================')
        self.stdout.write('DATOS CREADOS')
        self.stdout.write('============================')
        self.stdout.write(f'Mecánicos:   {Mecanico.objects.count()}')
        self.stdout.write(f'Clientes:   {Cliente.objects.count()}')
        self.stdout.write(f'Vehículos:  {Vehiculo.objects.count()}')
        self.stdout.write(f'Órdenes:    {OrdenTrabajo.objects.count()}')
        self.stdout.write(
            f'  Pendientes:    '
            f'{OrdenTrabajo.objects.filter(estado="Pendiente").count()}'
        )
        self.stdout.write(
            f'  En progreso:   '
            f'{OrdenTrabajo.objects.filter(estado="En progreso").count()}'
        )
        self.stdout.write(
            f'  Completadas:   '
            f'{OrdenTrabajo.objects.filter(estado="Completada").count()}'
        )
        self.stdout.write(
            f'  Canceladas:     '
            f'{OrdenTrabajo.objects.filter(estado="Cancelada").count()}'
        )
        self.stdout.write('============================')
