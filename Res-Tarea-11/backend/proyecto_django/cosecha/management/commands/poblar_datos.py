from datetime import date, timedelta
from random import choice, randint, uniform


from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from cosecha.models import Supervisor, Trabajador, Cuartel, RegistroCosecha


#comando para crear datos iniciales de prueba
class Command(BaseCommand):

    #descripcion del comando
    help = 'crea datos iniciales para probar roles y autenticacion'

    #ejecuta el comando principal
    def handle(self, *args, **options):

        #crea los grupos principales del sistema
        grupo_admin, _ = Group.objects.get_or_create(name='admin')
        grupo_supervisor, _ = Group.objects.get_or_create(name='supervisor')
        grupo_trabajador, _ = Group.objects.get_or_create(name='trabajador')

        #crea usuario administrador
        admin_user, creado_admin = User.objects.get_or_create(
            username='admin_huerto',
            defaults={
                'email': 'admin@huerto.cl',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        #asigna password solo cuando el usuario se crea por primera vez
        if creado_admin:
            admin_user.set_password('admin123')
            admin_user.save()

        admin_user.groups.add(grupo_admin)

        #crea usuarios supervisores
        supervisor_user_1, creado_sup_1 = User.objects.get_or_create(
            username='supervisor_norte',
            defaults={
                'email': 'supervisor.norte@huerto.cl',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if creado_sup_1:
            supervisor_user_1.set_password('supervisor123')
            supervisor_user_1.save()

        supervisor_user_1.groups.add(grupo_supervisor)

        supervisor_user_2, creado_sup_2 = User.objects.get_or_create(
            username='supervisor_sur',
            defaults={
                'email': 'supervisor.sur@huerto.cl',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if creado_sup_2:
            supervisor_user_2.set_password('supervisor123')
            supervisor_user_2.save()

        supervisor_user_2.groups.add(grupo_supervisor)

        #crea supervisores del huerto
        supervisor_norte, _ = Supervisor.objects.get_or_create(
            rut='11111111-1',
            defaults={
                'nombre': 'Supervisor Norte',
                'zona': 'Norte',
                'activo': True,
                'usuario': supervisor_user_1,
            }
        )

        supervisor_sur, _ = Supervisor.objects.get_or_create(
            rut='22222222-2',
            defaults={
                'nombre': 'Supervisor Sur',
                'zona': 'Sur',
                'activo': True,
                'usuario': supervisor_user_2,
            }
        )

                #crea supervisor este
        supervisor_este, _ = Supervisor.objects.get_or_create(
            rut='66666666-6',
            defaults={
                'nombre': 'Supervisor Este',
                'zona': 'Este',
                'activo': True,
            }
        )

        #crea supervisor oeste inactivo
        supervisor_oeste, _ = Supervisor.objects.get_or_create(
            rut='77777777-7',
            defaults={
                'nombre': 'Supervisor Oeste',
                'zona': 'Oeste',
                'activo': False,
            }
        )

        #crea usuario trabajador
        trabajador_user, creado_trabajador_user = User.objects.get_or_create(
            username='trabajador_juan',
            defaults={
                'email': 'trabajador.juan@huerto.cl',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if creado_trabajador_user:
            trabajador_user.set_password('trabajador123')
            trabajador_user.save()

        trabajador_user.groups.add(grupo_trabajador)

        #crea trabajadores de prueba
        Trabajador.objects.get_or_create(
            rut='33333333-3',
            defaults={
                'nombre': 'Juan Perez',
                'fecha_ingreso': date(2026, 1, 10),
                'activo': True,
                'supervisor': supervisor_norte,
                'usuario': trabajador_user,
            }
        )

        Trabajador.objects.get_or_create(
            rut='44444444-4',
            defaults={
                'nombre': 'Maria Soto',
                'fecha_ingreso': date(2026, 1, 15),
                'activo': True,
                'supervisor': supervisor_norte,
            }
        )

        Trabajador.objects.get_or_create(
            rut='55555555-5',
            defaults={
                'nombre': 'Pedro Rojas',
                'fecha_ingreso': date(2026, 1, 20),
                'activo': True,
                'supervisor': supervisor_sur,
            }
        )

                #crea trabajadores adicionales
        for numero in range(6, 23):

            supervisor = choice([
                supervisor_norte,
                supervisor_sur,
                supervisor_este,
                supervisor_oeste,
            ])

            Trabajador.objects.get_or_create(
                rut=f'9000000{numero}-{numero % 10}',
                defaults={
                    'nombre': f'Trabajador {numero}',
                    'fecha_ingreso': date(2026, 1, 1),
                    'activo': True,
                    'supervisor': supervisor,
                }
            )

        #crea cuarteles de prueba
        Cuartel.objects.get_or_create(
            nombre='Cuartel Norte 1',
            defaults={
                'hectareas': 3.5,
                'variedad': 'Duke',
                'activo': True,
                'supervisor': supervisor_norte,
            }
        )

        Cuartel.objects.get_or_create(
            nombre='Cuartel Norte 2',
            defaults={
                'hectareas': 4.0,
                'variedad': 'Legacy',
                'activo': True,
                'supervisor': supervisor_norte,
            }
        )

        Cuartel.objects.get_or_create(
            nombre='Cuartel Sur 1',
            defaults={
                'hectareas': 5.0,
                'variedad': 'Liberty',
                'activo': True,
                'supervisor': supervisor_sur,
            }
        )

                #crea cuarteles adicionales
        variedades = [
            'Duke',
            'Legacy',
            'Brigitta',
            'Liberty',
        ]

        for numero in range(4, 13):

            supervisor = choice([
                supervisor_norte,
                supervisor_sur,
                supervisor_este,
                supervisor_oeste,
            ])

            Cuartel.objects.get_or_create(
                nombre=f'Cuartel {numero}',
                defaults={
                    'hectareas': round(uniform(2, 8), 2),
                    'variedad': choice(variedades),
                    'activo': True,
                    'supervisor': supervisor,
                }
            )

        #obtiene trabajadores para registros de prueba
        juan = Trabajador.objects.get(rut='33333333-3')
        maria = Trabajador.objects.get(rut='44444444-4')
        pedro = Trabajador.objects.get(rut='55555555-5')

        #obtiene cuarteles para registros de prueba
        cuartel_norte_1 = Cuartel.objects.get(nombre='Cuartel Norte 1')
        cuartel_norte_2 = Cuartel.objects.get(nombre='Cuartel Norte 2')
        cuartel_sur_1 = Cuartel.objects.get(nombre='Cuartel Sur 1')

        #crea registros de cosecha respetando la cuadrilla
        RegistroCosecha.objects.get_or_create(
            trabajador=juan,
            cuartel=cuartel_norte_1,
            fecha=date(2026, 6, 10),
            defaults={
                'kilos': 120,
                'horas': 8,
                'calidad': 'Exportacion',
                'observaciones': 'registro inicial de prueba',
            }
        )

        RegistroCosecha.objects.get_or_create(
            trabajador=maria,
            cuartel=cuartel_norte_2,
            fecha=date(2026, 6, 10),
            defaults={
                'kilos': 95,
                'horas': 7,
                'calidad': 'Nacional',
                'observaciones': 'registro inicial de prueba',
            }
        )

        RegistroCosecha.objects.get_or_create(
            trabajador=pedro,
            cuartel=cuartel_sur_1,
            fecha=date(2026, 6, 10),
            defaults={
                'kilos': 110,
                'horas': 8,
                'calidad': 'Exportacion',
                'observaciones': 'registro inicial de prueba',
            }
        )
        #crea registros masivos de cosecha
        trabajadores = Trabajador.objects.select_related(
            'supervisor'
        )

        calidades = [
            RegistroCosecha.CALIDAD_EXPORTACION,
            RegistroCosecha.CALIDAD_NACIONAL,
            RegistroCosecha.CALIDAD_DESCARTE,
        ]

        for trabajador in trabajadores:

            cuarteles = Cuartel.objects.filter(
                supervisor=trabajador.supervisor
            )

            for dia in range(1, 21):

                fecha_registro = date(2026, 5, 1) + timedelta(days=dia)

                cuartel = choice(list(cuarteles))

                calidad = choice(calidades)

                RegistroCosecha.objects.get_or_create(
                    trabajador=trabajador,
                    cuartel=cuartel,
                    fecha=fecha_registro,
                    defaults={
                        'kilos': round(uniform(40, 180), 2),
                        'horas': round(uniform(4, 10), 2),
                        'calidad': calidad,
                        'observaciones': 'registro generado automaticamente',
                    }
                )

        #muestra resumen final
        self.stdout.write(self.style.SUCCESS('datos iniciales creados correctamente'))
        self.stdout.write('usuarios de prueba:')
        self.stdout.write('admin_huerto / admin123')
        self.stdout.write('supervisor_norte / supervisor123')
        self.stdout.write('supervisor_sur / supervisor123')
        self.stdout.write('trabajador_juan / trabajador123')
