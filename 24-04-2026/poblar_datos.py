import os
import sys
import django
import random
import time
from datetime import datetime, timedelta
from django.db import IntegrityError

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero, Cuartel, Labor

SEPARADOR = "=" * 64
t0 = time.time()

print("Limpiando datos.")

Labor.objects.all().delete()
Cuartel.objects.all().delete()

print("Datos anteriores limpiados")

cuarteles = [
    Cuartel(nombre="A-1", hectareas=5.50, variedad="Duke"),
    Cuartel(nombre="A-2", hectareas=8.25, variedad="Duke"),
    Cuartel(nombre="B-1", hectareas=12.00, variedad="Legacy"),
    Cuartel(nombre="B-2", hectareas=6.75, variedad="Brigitta"),
    Cuartel(nombre="C-1", hectareas=10.50, variedad="Legacy"),
    Cuartel(nombre="C-2", hectareas=4.00, variedad="Star"),
]

Cuartel.objects.bulk_create(cuarteles)

temporeros = list(Temporero.objects.filter(activo=True))
cuarteles = list(Cuartel.objects.all())

tipos_labor = ["Cosecha", "Poda", "Riego", "Pesticida", "Limpieza"]
observaciones_posibles = ["Sector norte","Lluvia leve","Turno tarde","Buen rendimiento",
]

labores_creadas = 0
duplicadas_saltadas = 0
conteo_por_temporero = {temporero.id: 0 for temporero in temporeros}

combinaciones = []

for temporero in temporeros:
    for cuartel in cuarteles:
        for tipo in tipos_labor:
            for i in range(30):
                fecha = datetime.now().date() - timedelta(days=i + 1)
                combinaciones.append((temporero, cuartel, tipo, fecha))
#antes, al ejecutar, tardaba 143seg y 19.000 duolicados
#asi que buscando una manera de optimizarlo enconctre suffer
#segun entiendo, evita duplicados, genera las combinaciones y toma las que son necesarias
#aunque de momento al ejecutar tard 30seg y bajo a 9.000 duplicados
random.shuffle(combinaciones)
def crear_labor(temporero, cuartel, tipo, fecha):
    global labores_creadas, duplicadas_saltadas

    horas = round(random.uniform(2, 10), 2)

    if tipo == "Cosecha":
        kilos = round(random.uniform(20, 150), 2)
    else:
        kilos = None

    observaciones = random.choice(observaciones_posibles) if random.random() < 0.2 else ""

    try:
        labor = Labor(
            temporero=temporero,
            cuartel=cuartel,
            tipo=tipo,
            fecha=fecha,
            horas_trabajadas=horas,
            kilos_cosechados=kilos,
            observaciones=observaciones
        )

        labor.full_clean()
        labor.save()

        labores_creadas += 1
        conteo_por_temporero[temporero.id] += 1

    except IntegrityError:
        duplicadas_saltadas += 1

    except Exception:
        duplicadas_saltadas += 1


# Primero asegura mínimo 5 labores por temporero activo
for temporero in temporeros:
    for combinacion in combinaciones:
        temp, cuartel, tipo, fecha = combinacion

        if temp.id == temporero.id and conteo_por_temporero[temporero.id] < 5:
            crear_labor(temp, cuartel, tipo, fecha)

        if conteo_por_temporero[temporero.id] >= 5:
            break


# Luego completa hasta llegar a 200, sin pasar de 25 por temporero
for temporero, cuartel, tipo, fecha in combinaciones:
    if labores_creadas >= 200:
        break

    if conteo_por_temporero[temporero.id] >= 25:
        continue

    crear_labor(temporero, cuartel, tipo, fecha)


temporeros_con_labores = Temporero.objects.filter(
    labores__isnull=False
).distinct().count()

t1 = time.time()
tiempo_total = t1 - t0

print(SEPARADOR)
print("DATOS POBLADOS CORRECTAMENTE")
print(SEPARADOR)
print(f"Cuarteles creados:              {Cuartel.objects.count()}")
print(f"Labores creadas:              {labores_creadas}")
print(f"Labores duplicadas saltadas:  {duplicadas_saltadas}")
print(f"Temporeros con labores:       {temporeros_con_labores}")
print(f"Tiempo total de ejecución:    {tiempo_total:.2f} segundos")
print(SEPARADOR)
