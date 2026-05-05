import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero, Cuartel, Labor
from django.db.models import Count, Sum, Avg, Q

# ============================================================
# Consulta 1: Labores del temporero por RUT
# ============================================================
labores = Labor.objects.filter(temporero__rut='11111111-1')

for l in labores:
    print(l.temporero.nombre, l.tipo, l.fecha)

# ============================================================
# Consulta 2: Labores usando relacion inversa
# ============================================================
temporero = Temporero.objects.get(rut='11111111-1')

labores = temporero.labores.all()

for l in labores:
    print(l.tipo, l.cuartel.nombre, l.fecha)

# ============================================================
# Consulta 3: Labores en cuarteles de variedad Duke
# ============================================================
labores = Labor.objects.filter(cuartel__variedad='Duke')

for l in labores:
    print(l.temporero.nombre, l.cuartel.nombre, l.tipo, l.fecha)

# ============================================================
# Consulta 4: Total de horas por temporero
# ============================================================
resultado = Temporero.objects.filter(activo=True).annotate(
    total_horas=Sum('labores__horas_trabajadas')
).order_by('-total_horas')

for t in resultado:
    print(t.nombre, t.rut, t.total_horas)

# ============================================================
# Consulta 5: Cuartel mas productivo
# ============================================================
resultado = Cuartel.objects.annotate(
    total_kilos=Sum('labores__kilos_cosechados')
).filter(
    total_kilos__isnull=False
).order_by('-total_kilos').first()

if resultado:
    print("Cuartel más productivo:")
    print(resultado.nombre, round(resultado.total_kilos, 2))
else:
    print("No hay datos de cosecha")
# ============================================================
# Consulta 6: Ranking de tipos de labor
# ============================================================
resultado = Labor.objects.values('tipo').annotate(
    cantidad=Count('id')
).order_by('-cantidad')
total_labores = Labor.objects.count()

for r in resultado:
    porcentaje = (r['cantidad'] / total_labores) * 100
    print(r['tipo'], r['cantidad'], f"{porcentaje:.2f}%")

# ============================================================
# Consulta 7: Promedio kilos de cosecha por cuartel
# ============================================================
resultado = Cuartel.objects.annotate(
    promedio_kilos=Avg(
        'labores__kilos_cosechados',
        filter=Q(labores__tipo='Cosecha')
    )
).filter(
    promedio_kilos__isnull=False
).order_by('-promedio_kilos')

for c in resultado:
    print(c.nombre, f"{c.promedio_kilos:.2f}")

# ============================================================
# Consulta 8: Temporeros sin labores e la ultima semana
# ============================================================
from datetime import datetime, timedelta
hace_7_dias = datetime.now().date() - timedelta(days=7)

resultado = Temporero.objects.filter(activo=True).annotate(
    labores_recientes=Count(
        'labores',
        filter=Q(labores__fecha__gte=hace_7_dias)
    )
).filter(labores_recientes=0)

for t in resultado:
    print(t.nombre, t.rut)

# ============================================================
# Consulta 9: 3 Temporeros cosecheros del mes
# ============================================================
hace_30_dias = datetime.now().date() - timedelta(days=30)

resultado = Temporero.objects.annotate(
    total_kilos=Sum(
        'labores__kilos_cosechados',
        filter=Q(
            labores__tipo='Cosecha',
            labores__fecha__gte=hace_30_dias
        )
    ),
    cantidad_labores=Count(
        'labores',
        filter=Q(
            labores__tipo='Cosecha',
            labores__fecha__gte=hace_30_dias
        )
    )
).filter(
    total_kilos__isnull=False
).order_by('-total_kilos')[:3]

for t in resultado:
    print(t.nombre, round(t.total_kilos, 2), t.cantidad_labores)

# ============================================================
# Consulta 10: Reporte cruzado
# ============================================================
resultado = Labor.objects.values('cuartel__nombre', 'tipo').annotate(
	cantidad=Count('id')
)

matriz = {}

for r in resultado:
	cuartel = r['cuartel__nombre']
	tipo = r['tipo']
	cantidad = r['cantidad']

	if cuartel not in matriz:
		matriz[cuartel] = {}

	matriz[cuartel][tipo] = cantidad

print("Matriz, cuartel y tipos de labores")

for cuartel, datos in matriz.items():
	print(f"{cuartel}: ", end="")

	for tipo, cantidad in datos.items():
		print(f"{tipo}={cantidad} ", end="")
	print()
