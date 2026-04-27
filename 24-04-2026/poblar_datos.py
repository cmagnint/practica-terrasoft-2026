import os
import sys
import django
import random
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero, Cuartel, Labor

print("Limpiando datos")

Labor.objects.all().delete()
Cuartel.objects.all().delete()

print("Datos limpiados")

cuarteles = [
    Cuartel(nombre="A-1", hectareas=5.50, variedad="Duke"),
    Cuartel(nombre="A-2", hectareas=8.25, variedad="Duke"),
    Cuartel(nombre="B-1", hectareas=12.00, variedad="Legacy"),
    Cuartel(nombre="B-2", hectareas=6.75, variedad="Brigitta"),
    Cuartel(nombre="C-1", hectareas=10.50, variedad="Legacy"),
    Cuartel(nombre="C-2", hectareas=4.00, variedad="Star"),
]

Cuartel.objects.bulk_create(cuarteles)

print("Cuarteles creados")

temporeros = list(Temporero.objects.filter(activo=True))
cuarteles = list(Cuartel.objects.all())

print("Generando labores")

labores_creadas = 0

from django.db import IntegrityError

tipos_labor = ['Cosecha', 'Poda', 'Riego', 'Pesticida', 'Limpieza']
observaciones_posibles = ["Sector norte", "Lluvia leve", "Turno tarde", "Buen rendimiento"]

labores_creadas = 0
duplicadas_saltadas = 0

while labores_creadas < 200:
    temporero = random.choice(temporeros)
    cuartel = random.choice(cuarteles)

    tipo = random.choices(
        tipos_labor,
        weights=[60, 10, 10, 10, 10],
        k=1
    )[0]

    fecha = datetime.now().date() - timedelta(days=random.randint(1, 30))
    horas = round(random.uniform(2, 10), 2)

    if tipo == 'Cosecha':
        kilos = round(random.uniform(20, 150), 2)
    else:
        kilos = None

    observaciones = random.choice(observaciones_posibles) if random.random() < 0.2 else ""

    try:
        Labor.objects.create(
            temporero=temporero,
            cuartel=cuartel,
            tipo=tipo,
            fecha=fecha,
            horas_trabajadas=horas,
            kilos_cosechados=kilos,
            observaciones=observaciones
        )
        labores_creadas += 1

    except IntegrityError:
        duplicadas_saltadas += 1

print("Labores creadas:", labores_creadas)
print("Duplicadas saltadas:", duplicadas_saltadas)
