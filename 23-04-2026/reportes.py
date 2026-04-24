import os
import django
import sys
from django.db.models import Count
from django.db.models import Count, Avg, F, ExpressionWrapper, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Now, ExtractYear

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero


print("\n===== RESUMEN GENERAL =====")

total = Temporero.objects.count()
activos = Temporero.objects.filter(activo=True).count()
inactivos = Temporero.objects.filter(activo=False).count()

print("Total temporeros:", total)
print("Activos:", activos)
print("Inactivos:", inactivos)

print("\n===== DISTRIBUCION POR TALLAS =====")

for t in Temporero.objects.values('talla_polera').annotate(total=Count('id')).order_by('-total'):
    print(f"Talla {t['talla_polera']}: {t['total']}")

print("\n===== RANGOS DE EDAD =====")

edad = ExpressionWrapper(
    ExtractYear(Now()) - ExtractYear(F('fecha_nacimiento')),
    output_field=IntegerField()
)

rangos = Temporero.objects.filter(activo=True).annotate(
    edad_calculada=edad
).annotate(
    rango=Case(
        When(edad_calculada__lt=30, then=Value("Menores de 30")),
        When(edad_calculada__gte=30, edad_calculada__lte=50, then=Value("Entre 30 y 50")),
        When(edad_calculada__gt=50, then=Value("Mayores de 50")),
        output_field=CharField()
    )
).values('rango').annotate(total=Count('id')).order_by('rango')

for r in rangos:
    print(f"{r['rango']}: {r['total']}")

print("\n===== DATOS DESTACADOS =====")

joven = Temporero.objects.order_by('-fecha_nacimiento').first()

antiguo = Temporero.objects.order_by('fecha_ingreso').first()

sin_telefono = Temporero.objects.filter(telefono__isnull=True).count()

print("Más joven:", joven.nombre)
print("Más antiguo:", antiguo.nombre)
print("Sin teléfono:", sin_telefono)


print("\n===== ALERTAS =====")

sin_telefono = Temporero.objects.filter(activo=True, telefono__isnull=True)

if sin_telefono.exists():
    print(f"Temporeros activos sin teléfono: {sin_telefono.count()}")
    for t in sin_telefono:
        print("-", t.nombre)
else:
    print("Sin alertas")
