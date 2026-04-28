import os
import sys
import django
import argparse
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), "proyecto_django"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campo.settings")
django.setup()

from temporeros.models import Temporero, Cuartel, Labor
from django.db.models import Count, Sum, Avg, Q, F, ExpressionWrapper, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Now, ExtractYear

SEPARADOR = "=" * 64

edad = ExpressionWrapper(
    ExtractYear(Now()) - ExtractYear(F("fecha_nacimiento")),
    output_field=IntegerField()
)

def separador():
    print(SEPARADOR)

def encabezado():
    ahora = datetime.now()
    separador()
    print(f"REPORTE DE TEMPOREROS - Generado el {ahora.strftime('%d/%m/%Y')} a las {ahora.strftime('%H:%M')}")
    separador()

def seccion_resumen_general():
    print("\n--- RESUMEN GENERAL ---")
    print(f"Total registrados:        {Temporero.objects.count()}")
    print(f"Activos:                  {Temporero.objects.filter(activo=True).count()}")
    print(f"Inactivos:                {Temporero.objects.filter(activo=False).count()}")
    print(f"Supervisores activos:     {Temporero.objects.filter(activo=True, supervisor=True).count()}")
    separador()

def seccion_distribucion_talla():
    print("\n--- DISTRIBUCIÓN POR TALLA ---")

    total_activos = Temporero.objects.filter(activo=True).count()

    resultado = Temporero.objects.filter(activo=True).values("talla_polera").annotate(
        cantidad=Count("id")
    ).order_by("-cantidad")

    print(f"{'TALLA':<8} {'CANTIDAD':>8} {'PORCENTAJE':>12}")

    for r in resultado:
        porcentaje = (r["cantidad"] / total_activos * 100) if total_activos else 0
        print(f"{r['talla_polera']:<8} {r['cantidad']:>8} {porcentaje:>10.1f}%")

    separador()

def seccion_rangos_edad():
    print("\n--- RANGOS DE EDAD ---")

    total_activos = Temporero.objects.filter(activo=True).count()

    resultado = Temporero.objects.filter(activo=True).annotate(
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

    for r in resultado:
        porcentaje = (r["cantidad"] / total_activos * 100) if total_activos else 0
        print(f"{r['rango']:<20} {r['cantidad']:>5} {porcentaje:>10.1f}%")

    separador()

def seccion_datos_destacados(solo_activos=False):
    print("\n--- DATOS DESTACADOS ---")

    base = Temporero.objects.filter(activo=True) if solo_activos else Temporero.objects.all()
    base_edad = base.annotate(edad_calculada=edad)

    antiguo = base.order_by("fecha_ingreso").first()
    joven = base_edad.order_by("-fecha_nacimiento").first()
    viejo = base_edad.order_by("fecha_nacimiento").first()
    promedio = base_edad.aggregate(promedio=Avg("edad_calculada"))["promedio"]

    if antiguo:
        print(f"Más antiguo en la empresa: {antiguo.nombre} - ingreso {antiguo.fecha_ingreso}")

    if joven:
        print(f"Más joven:                 {joven.nombre} - {joven.edad_calculada} años")

    if viejo:
        print(f"Más viejo:                 {viejo.nombre} - {viejo.edad_calculada} años")

    if promedio is not None:
        print(f"Promedio edad activos:     {promedio:.1f}")

    separador()

def seccion_resumen_labores(dias):
    print(f"\n--- RESUMEN DE LABORES (últimos {dias} días) ---")

    fecha_inicio = datetime.now().date() - timedelta(days=dias)
    labores = Labor.objects.filter(fecha__gte=fecha_inicio)

    total_labores = labores.count()
    total_horas = labores.aggregate(total=Sum("horas_trabajadas"))["total"] or 0
    total_kilos = labores.aggregate(total=Sum("kilos_cosechados"))["total"] or 0

    cosecha = labores.filter(tipo="Cosecha").count()
    otras = total_labores - cosecha

    pct_cosecha = (cosecha / total_labores * 100) if total_labores else 0
    pct_otras = (otras / total_labores * 100) if total_labores else 0

    print(f"Total de labores:             {total_labores}")
    print(f"Total de horas trabajadas:    {total_horas:.2f}")
    print(f"Total de kilos cosechados:    {total_kilos:.2f}")
    print(f"Labores de cosecha:           {cosecha} ({pct_cosecha:.1f}%)")
    print(f"Labores de otras tareas:      {otras} ({pct_otras:.1f}%)")

    separador()

def seccion_top_horas(dias):
    print(f"\n--- TOP 5 TEMPOREROS POR HORAS (últimos {dias} días) ---")

    fecha_inicio = datetime.now().date() - timedelta(days=dias)

    resultado = Temporero.objects.annotate(
        total_horas=Sum(
            "labores__horas_trabajadas",
            filter=Q(labores__fecha__gte=fecha_inicio)
        ),
        cantidad_labores=Count(
            "labores",
            filter=Q(labores__fecha__gte=fecha_inicio)
        )
    ).filter(
        total_horas__isnull=False
    ).order_by("-total_horas")[:5]

    print(f"{'NOMBRE':<25} {'HORAS':>8} {'LABORES':>8}")

    for t in resultado:
        print(f"{t.nombre:<25} {t.total_horas:>8.2f} {t.cantidad_labores:>8}")

    separador()

def seccion_productividad_cuartel(dias):
    print("\n--- PRODUCTIVIDAD POR CUARTEL ---")

    fecha_inicio = datetime.now().date() - timedelta(days=dias)

    resultado = Cuartel.objects.annotate(
        total_kilos=Sum(
            "labores__kilos_cosechados",
            filter=Q(labores__tipo="Cosecha", labores__fecha__gte=fecha_inicio)
        )
    ).filter(
        total_kilos__isnull=False
    ).order_by("-total_kilos")

    print(f"{'CUARTEL':<10} {'HECTÁREAS':>10} {'KILOS TOTAL':>15} {'KG/HECTÁREA':>15}")

    for c in resultado:
        productividad = c.total_kilos / c.hectareas if c.hectareas else 0
        print(f"{c.nombre:<10} {c.hectareas:>10.2f} {c.total_kilos:>15.2f} {productividad:>15.2f}")

    separador()

def seccion_alertas(dias):
    print("\n--- ALERTAS ---")

    hubo_alertas = False
    fecha_7_dias = datetime.now().date() - timedelta(days=7)

    sin_telefono = Temporero.objects.filter(activo=True, telefono__isnull=True)

    if sin_telefono.exists():
        hubo_alertas = True
        print(f"emporeros activos sin teléfono: {sin_telefono.count()}")
        for t in sin_telefono:
            print(f"   - {t.nombre}")

    sin_contacto = Temporero.objects.filter(activo=True, contacto_emergencia__isnull=True)

    if sin_contacto.exists():
        hubo_alertas = True
        print(f"emporeros activos sin contacto de emergencia: {sin_contacto.count()}")
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
        print(f"upervisores activos menores de 25 años: {supervisores_jovenes.count()}")
        for t in supervisores_jovenes:
            print(f"   - {t.nombre} ({t.edad_calculada} años)")

    sin_labores = Temporero.objects.filter(activo=True).annotate(
        labores_recientes=Count(
            "labores",
            filter=Q(labores__fecha__gte=fecha_7_dias)
        )
    ).filter(labores_recientes=0)

    if sin_labores.exists():
        hubo_alertas = True
        print(f"emporeros activos sin labores en los últimos 7 días: {sin_labores.count()}")
        for t in sin_labores:
            print(f"   - {t.nombre}")

    cuarteles_sin_labores = Cuartel.objects.filter(activo=True).annotate(
        labores_recientes=Count(
            "labores",
            filter=Q(labores__fecha__gte=fecha_7_dias)
        )
    ).filter(labores_recientes=0)

    if cuarteles_sin_labores.exists():
        hubo_alertas = True
        print(f"uarteles activos sin labores en los últimos 7 días: {cuarteles_sin_labores.count()}")
        for c in cuarteles_sin_labores:
            print(f"   - {c.nombre}")

    sobrecarga = Temporero.objects.filter(activo=True).annotate(
        horas_semana=Sum(
            "labores__horas_trabajadas",
            filter=Q(labores__fecha__gte=fecha_7_dias)
        )
    ).filter(horas_semana__gt=60)

    if sobrecarga.exists():
        hubo_alertas = True
        print(f"emporero con más de 60 horas en la última semana: {sobrecarga.count()}")
        for t in sobrecarga:
            print(f"   - {t.nombre} ({t.horas_semana:.2f} horas)")

    if not hubo_alertas:
        print("Sin alertas.")

    separador()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-activos", action="store_true")
    parser.add_argument("--dias", type=int, default=30)
    args = parser.parse_args()

    encabezado()

    if not args.solo_activos:
        seccion_resumen_general()

    seccion_distribucion_talla()
    seccion_rangos_edad()
    seccion_datos_destacados(solo_activos=args.solo_activos)
    seccion_alertas(args.dias)

    seccion_resumen_labores(args.dias)
    seccion_top_horas(args.dias)
    seccion_productividad_cuartel(args.dias)

if __name__ == "__main__":
    main()
