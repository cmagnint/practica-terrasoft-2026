import os
import sys
import django
import argparse
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'proyecto_django'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo.settings')
django.setup()

from temporeros.models import Temporero
from django.db.models import Count, Avg, F, ExpressionWrapper, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Now, ExtractYear

SEPARADOR = "=" * 64

edad = ExpressionWrapper(
    ExtractYear(Now()) - ExtractYear(F("fecha_nacimiento")),
    output_field=IntegerField()
)

def imprimir_encabezado():
    ahora = datetime.now()
    print(SEPARADOR)
    print(f"Reporte de temporeros generado el {ahora.strftime('%d/%m/%Y')} a las {ahora.strftime('%H:%M')}")
    print(SEPARADOR)

def seccion_resumen_general():
    print("\n--- RESUMEN GENERAL ---")
    total = Temporero.objects.count()
    activos = Temporero.objects.filter(activo=True).count()
    inactivos = Temporero.objects.filter(activo=False).count()
    supervisores_activos = Temporero.objects.filter(activo=True, supervisor=True).count()

    print(f"Total registrados:    {total}")
    print(f"Activos:              {activos}")
    print(f"Inactivos:            {inactivos}")
    print(f"Supervisores activos: {supervisores_activos}")
    print(SEPARADOR)

def seccion_distribucion_talla():
    print("\n--- DISTRIBUCIÓN POR TALLA ---")

    total_activos = Temporero.objects.filter(activo=True).count()

    tallas = Temporero.objects.filter(activo=True).values("talla_polera").annotate(
        cantidad=Count("id")
    ).order_by("-cantidad")

    print(f"{'TALLA':<8} {'CANTIDAD':>8} {'PORCENTAJE':>12}")

    for t in tallas:
        talla = t["talla_polera"]
        cantidad = t["cantidad"]
        porcentaje = (cantidad / total_activos * 100) if total_activos else 0
        print(f"{talla:<8} {cantidad:>8} {porcentaje:>10.1f}%")

    print(SEPARADOR)

def seccion_rangos_edad():
    print("\n--- RANGOS DE EDAD ---")

    total_activos = Temporero.objects.filter(activo=True).count()

    rangos = Temporero.objects.filter(activo=True).annotate(
        edad_calculada=edad
    ).annotate(
        rango=Case(
            When(edad_calculada__lt=25, then=Value("Menores de 25")),
            When(edad_calculada__gte=25, edad_calculada__lte=40, then=Value("Entre 25 y 40")),
            When(edad_calculada__gte=41, edad_calculada__lte=55, then=Value("Entre 41 y 55")),
            When(edad_calculada__gt=55, then=Value("Mayores de 55")),
            output_field=CharField()
        )
    ).values("rango").annotate(
        cantidad=Count("id")
    ).order_by("rango")

    for r in rangos:
        porcentaje = (r["cantidad"] / total_activos * 100) if total_activos else 0
        print(f"{r['rango']:<20} {r['cantidad']:>5} {porcentaje:>10.1f}%")

    print(SEPARADOR)

def seccion_datos_destacados(solo_activos=False):
    print("\n--- DATOS DESTACADOS ---")

    base = Temporero.objects.filter(activo=True) if solo_activos else Temporero.objects.all()

    base_con_edad = base.annotate(edad_calculada=edad)

    antiguo = base.order_by("fecha_ingreso").first()
    joven = base_con_edad.order_by("-fecha_nacimiento").first()
    viejo = base_con_edad.order_by("fecha_nacimiento").first()
    promedio = base_con_edad.aggregate(promedio=Avg("edad_calculada"))["promedio"]

    if antiguo:
        print(f"Más antiguo:     {antiguo.nombre} - ingreso {antiguo.fecha_ingreso}")

    if joven:
        print(f"Más joven:       {joven.nombre} - {joven.edad_calculada} años")

    if viejo:
        print(f"Más viejo:       {viejo.nombre} - {viejo.edad_calculada} años")

    if promedio is not None:
        print(f"Promedio edad activos: {promedio:.1f}")

    print(SEPARADOR)

def seccion_alertas():
    print("\n--- ALERTAS ---")

    hubo_alertas = False

    sin_telefono = Temporero.objects.filter(activo=True, telefono__isnull=True)
    if sin_telefono.exists():
        hubo_alertas = True
        print(f"emporeros activos sin teléfono: {sin_telefono.count()}")
        for t in sin_telefono:
            print(f"   - {t.nombre}")

    sin_contacto = Temporero.objects.filter(activo=True, contacto_emergencia__isnull=True)
    if sin_contacto.exists():
        hubo_alertas = True
        print(f"\n Temporeros activos sin contacto de emergencia: {sin_contacto.count()}")
        for t in sin_contacto:
            print(f"   - {t.nombre}")

    supervisores_jovenes = Temporero.objects.filter(
        activo=True,
        supervisor=True
    ).annotate(
        edad_calculada=edad
    ).filter(
        edad_calculada__lt=25
    )

    if supervisores_jovenes.exists():
        hubo_alertas = True
        print(f"\n Supervisores activos menores de 25 años: {supervisores_jovenes.count()}")
        for t in supervisores_jovenes:
            print(f"   - {t.nombre} ({t.edad_calculada} años)")

    if not hubo_alertas:
        print("No hay alertas.")

    print(SEPARADOR)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-activos", action="store_true")
    args = parser.parse_args()

    imprimir_encabezado()

    if not args.solo_activos:
        seccion_resumen_general()

    seccion_distribucion_talla()
    seccion_rangos_edad()
    seccion_datos_destacados(solo_activos=args.solo_activos)
    seccion_alertas()

if __name__ == "__main__":
    main()
