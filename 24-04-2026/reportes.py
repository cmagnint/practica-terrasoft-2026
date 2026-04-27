import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero, Cuartel, Labor
from django.db.models import Count, Sum, Avg, Q
from datetime import datetime, timedelta

print("Resumen de labores en los ultimos 30 dias")

hace_30_dias = datetime.now().date() - timedelta(days=30)

labores = Labor.objects.filter(fecha__gte=hace_30_dias)

total_labores = labores.count()
total_horas = labores.aggregate(total=Sum('horas_trabajadas'))['total'] or 0
total_kilos = labores.aggregate(total=Sum('kilos_cosechados'))['total'] or 0

cosecha = labores.filter(tipo='Cosecha').count()
otras = total_labores - cosecha

porc_cosecha = (cosecha / total_labores * 100) if total_labores else 0
porc_otras = (otras / total_labores * 100) if total_labores else 0

print(f"Total de labores: {total_labores}")
print(f"Total de horas trabajadas: {round(total_horas,2)}")
print(f"Total de kilos cosechados: {round(total_kilos,2)}")
print(f"Labores de cosecha: {cosecha} ({porc_cosecha:.2f}%)")
print(f"Labores de otras tareas: {otras} ({porc_otras:.2f}%)")

print("Top 5 temporeros por horas en los ultimos 30 dias")

top = Temporero.objects.annotate(
    total_horas=Sum(
        'labores__horas_trabajadas',
        filter=Q(labores__fecha__gte=hace_30_dias)
    ),
    total_labores=Count(
        'labores',
        filter=Q(labores__fecha__gte=hace_30_dias)
    )
).filter(
    total_horas__isnull=False
).order_by('-total_horas')[:5]

for t in top:
    print(f"{t.nombre:20} {round(t.total_horas,2):8} {t.total_labores}")

print("Productividad por cuartel")

cuarteles = Cuartel.objects.annotate(
    total_kilos=Sum(
        'labores__kilos_cosechados',
        filter=Q(labores__tipo='Cosecha', labores__fecha__gte=hace_30_dias)
    )
).filter(
    total_kilos__isnull=False
).order_by('-total_kilos')

print(f"{'CUARTEL':10} {'HECTÁREAS':10} {'KILOS':12} {'KG/HECTÁREA'}")

for c in cuarteles:
    productividad = c.total_kilos / c.hectareas if c.hectareas else 0
    print(f"{c.nombre:10} {c.hectareas:10} {round(c.total_kilos,2):12} {round(productividad,2)}")

print("Alertas")

hace_7_dias = datetime.now().date() - timedelta(days=7)

sin_labores = Temporero.objects.filter(activo=True).annotate(
    labores_recientes=Count(
        'labores',
        filter=Q(labores__fecha__gte=hace_7_dias)
    )
).filter(labores_recientes=0)

if sin_labores.exists():
    print("emporeros sin labores en úlos ltimos 7 días:")
    for t in sin_labores:
        print("-", t.nombre)
else:
    print("Todos los temporeros tienen labores")

sobrecarga = Temporero.objects.annotate(
    horas_semana=Sum(
        'labores__horas_trabajadas',
        filter=Q(labores__fecha__gte=hace_7_dias)
    )
).filter(horas_semana__gt=60)

if sobrecarga.exists():
    print("emporeros con sobrecarga ")
    for t in sobrecarga:
        print(f"- {t.nombre} ({round(t.horas_semana,2)} hrs)")
else:
    print("No hay sobrecarga laboral")
