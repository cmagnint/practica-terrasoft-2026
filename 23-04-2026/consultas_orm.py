#temporada_django=> \dt
#                 List of relations
#Schema |            Name            | Type  | Owner
#-------+----------------------------+-------+-------
#public | auth_group                 | table | admin
#public | auth_group_permissions     | table | admin
#public | auth_permission            | table | admin
#public | auth_user                  | table | admin
#public | auth_user_groups           | table | admin
#public | auth_user_user_permissions | table | admin
#public | django_admin_log           | table | admin
#public | django_content_type        | table | admin
#public | django_migrations          | table | admin
#public | django_session             | table | admin
#public | temporeros_temporero       | table | admin

#temporada_django=> \d
#                      List of relations
#Schema |               Name                |   Type   | Owner
#-------+-----------------------------------+----------+-------
#public | auth_group                        | table    | admin
#public | auth_group_id_seq                 | sequence | admin
#public | auth_group_permissions            | table    | admin
#public | auth_group_permissions_id_seq     | sequence | admin
#public | auth_permission                   | table    | admin
#public | auth_permission_id_seq            | sequence | admin
#public | auth_user                         | table    | admin
#public | auth_user_groups                  | table    | admin
#public | auth_user_groups_id_seq           | sequence | admin
#public | auth_user_id_seq                  | sequence | admin
#public | auth_user_user_permissions        | table    | admin
#public | auth_user_user_permissions_id_seq | sequence | admin
#public | django_admin_log                  | table    | admin
#public | django_admin_log_id_seq           | sequence | admin
#public | django_content_type               | table    | admin
#public | django_content_type_id_seq        | sequence | admin
#public | django_migrations                 | table    | admin
#public | django_migrations_id_seq          | sequence | admin
#public | django_session                    | table    | admin
#public | temporeros_temporero              | table    | admin
#public | temporeros_temporero_id_seq       | sequence | admin



# ================================
# CONSULTAS ORM - TEMPOREROS
# ================================

from temporeros.models import Temporero
from django.db.models import Q, Count, Avg, F, ExpressionWrapper, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Now, ExtractYear


#1- Listar temporeros activos ordenados por fecha de ingreso (más nuevo primero)
temporeros = Temporero.objects.filter(activo=True).order_by('-fecha_ingreso')

print("\n--- Temporeros activos ordenados ---")
for t in temporeros:
    print(t.nombre, t.fecha_ingreso)


#2- Buscar temporero por RUT con manejo de error
print("\n--- Buscar temporero por RUT ---")
try:
    t = Temporero.objects.get(rut="11111111-1")
    print(t.nombre, t.rut)
except Temporero.DoesNotExist:
    print("Temporero no encontrado")


#3- Contar supervisores activos
print("\n--- Supervisores activos ---")
cantidad = Temporero.objects.filter(supervisor=True, activo=True).count()
print("Cantidad:", cantidad)


#4- Marcar un temporero como inactivo
print("\n--- Marcar temporero como inactivo ---")
Temporero.objects.filter(rut="11111111-1").update(activo=False)

t = Temporero.objects.get(rut="11111111-1")
print(t.nombre, t.activo)


#5- Nombres que empiezan con J o M
print("\n--- Nombres con J o M ---")
for t in Temporero.objects.filter(
    Q(nombre__istartswith='j') | Q(nombre__istartswith='m')
):
    print(t.nombre)


#6- Cantidad por talla de polera
print("\n--- Cantidad por talla ---")
for t in Temporero.objects.values('talla_polera').annotate(total=Count('id')).order_by('-total'):
    print(t['talla_polera'], t['total'])


#7- Promedio de edad (supervisores vs no supervisores)
edad = ExpressionWrapper(
    ExtractYear(Now()) - ExtractYear(F('fecha_nacimiento')),
    output_field=IntegerField()
)

print("\n--- Promedio de edad ---")
sup = Temporero.objects.filter(supervisor=True).aggregate(promedio=Avg(edad))
no_sup = Temporero.objects.filter(supervisor=False).aggregate(promedio=Avg(edad))

print("Supervisores:", sup)
print("No supervisores:", no_sup)


#8- Agrupación por rangos de edad
print("\n--- Rangos de edad ---")

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
    print(r['rango'], r['total'])
