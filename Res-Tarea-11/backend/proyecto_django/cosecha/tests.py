from datetime import date
from urllib.parse import quote

from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase

from cosecha.models import (
    Supervisor,
    Trabajador,
    Cuartel,
    RegistroCosecha,
    AuditLog,
)


#tests principales de la api de cosecha
class CosechaAPITestCase(APITestCase):

    #prepara datos base para cada test
    def setUp(self):

        #crea grupos de roles
        self.grupo_admin = Group.objects.create(name='admin')
        self.grupo_supervisor = Group.objects.create(name='supervisor')
        self.grupo_trabajador = Group.objects.create(name='trabajador')

        #crea usuarios
        self.admin = User.objects.create_user(
            username='admin_test',
            password='admin123'
        )
        self.admin.groups.add(self.grupo_admin)

        self.user_supervisor_a = User.objects.create_user(
            username='supervisor_a',
            password='supervisor123'
        )
        self.user_supervisor_a.groups.add(self.grupo_supervisor)

        self.user_supervisor_b = User.objects.create_user(
            username='supervisor_b',
            password='supervisor123'
        )
        self.user_supervisor_b.groups.add(self.grupo_supervisor)

        self.user_trabajador = User.objects.create_user(
            username='trabajador_test',
            password='trabajador123'
        )
        self.user_trabajador.groups.add(self.grupo_trabajador)

        #crea supervisores
        self.supervisor_a = Supervisor.objects.create(
            nombre='Supervisor A',
            rut='11111111-1',
            zona='Norte',
            usuario=self.user_supervisor_a
        )

        self.supervisor_b = Supervisor.objects.create(
            nombre='Supervisor B',
            rut='22222222-2',
            zona='Sur',
            usuario=self.user_supervisor_b
        )

        #crea trabajadores
        self.trabajador_a = Trabajador.objects.create(
            nombre='Trabajador A',
            rut='33333333-3',
            fecha_ingreso=date(2026, 1, 1),
            supervisor=self.supervisor_a,
            usuario=self.user_trabajador
        )

        self.trabajador_b = Trabajador.objects.create(
            nombre='Trabajador B',
            rut='44444444-4',
            fecha_ingreso=date(2026, 1, 1),
            supervisor=self.supervisor_b
        )

        #crea cuarteles
        self.cuartel_a = Cuartel.objects.create(
            nombre='Cuartel A',
            hectareas=3.5,
            variedad='Duke',
            supervisor=self.supervisor_a
        )

        self.cuartel_b = Cuartel.objects.create(
            nombre='Cuartel B',
            hectareas=4.0,
            variedad='Legacy',
            supervisor=self.supervisor_b
        )

        #crea registros
        self.registro_a = RegistroCosecha.objects.create(
            trabajador=self.trabajador_a,
            cuartel=self.cuartel_a,
            fecha=date(2026, 6, 1),
            kilos=100,
            horas=8,
            calidad='Exportacion'
        )

        self.registro_b = RegistroCosecha.objects.create(
            trabajador=self.trabajador_b,
            cuartel=self.cuartel_b,
            fecha=date(2026, 6, 1),
            kilos=90,
            horas=7,
            calidad='Nacional'
        )

    #verifica que el endpoint health responda correctamente
    def test_health_endpoint(self):

        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)

    #verifica login de administrador
    def test_login_admin(self):

        response = self.client.post(
            '/api/auth/login/',
            {
                'username': 'admin_test',
                'password': 'admin123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    #verifica que el administrador vea trabajadores
    def test_admin_puede_ver_trabajadores(self):

        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/trabajadores/')
        self.assertEqual(response.status_code, 200)

    #verifica que el trabajador vea solo sus registros
    def test_trabajador_ve_sus_registros(self):

        self.client.force_authenticate(self.user_trabajador)
        response = self.client.get('/api/registros/')
        self.assertEqual(response.status_code, 200)

    #verifica que el resumen responda correctamente
    def test_resumen_registros(self):

        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/registros/resumen/')
        self.assertEqual(response.status_code, 200)

    #verifica productividad de un cuartel
    #verifica productividad de un cuartel
    def test_productividad_cuartel(self):

        self.client.force_authenticate(self.admin)

        nombre_cuartel = quote(self.cuartel_a.nombre)

        response = self.client.get(
            f'/api/cuarteles/{nombre_cuartel}/productividad/'
        )

        self.assertEqual(response.status_code, 200)

    #verifica rendimiento de un trabajador
    def test_rendimiento_trabajador(self):

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            f'/api/trabajadores/{self.trabajador_a.rut}/rendimiento/'        )
        self.assertEqual(response.status_code, 200)

    #verifica que se cree un registro correctamente
    def test_crear_registro(self):

        self.client.force_authenticate(self.user_supervisor_a)

        response = self.client.post(
            '/api/registros/',
            {
                'trabajador': self.trabajador_a.id,
                'cuartel': self.cuartel_a.id,
                'fecha': '2026-06-02',
                'kilos': 120,
                'horas': 8,
                'calidad': 'Exportacion',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)

    #verifica regla cruzada trabajador cuartel
    def test_regla_cuadrilla_invalida(self):

        self.client.force_authenticate(self.user_supervisor_a)
        response = self.client.post(
            '/api/registros/',
            {
                'trabajador': self.trabajador_a.id,
                'cuartel': self.cuartel_b.id,
                'fecha': '2026-06-03',
                'kilos': 100,
                'horas': 8,
                'calidad': 'Exportacion',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)

    #verifica que exista auditoria
    def test_auditoria_registro(self):

        AuditLog.objects.create(
            usuario=self.admin,
            accion='prueba',
            modelo='RegistroCosecha',
            objeto_id='1'
        )

        self.assertEqual(
            AuditLog.objects.count(),
            1
        )

    #verifica que un request sin token sea rechazado
    def test_request_sin_token_da_401(self):

        response = self.client.get('/api/trabajadores/')
        self.assertEqual(response.status_code, 401)

    #verifica que supervisor a no vea trabajadores de supervisor b
    def test_supervisor_no_ve_trabajadores_de_otra_cuadrilla(self):

        self.client.force_authenticate(self.user_supervisor_a)

        response = self.client.get('/api/trabajadores/')

        self.assertEqual(response.status_code, 200)

        ids = [
            trabajador['id']
            for trabajador in response.data['results']
        ]

        self.assertIn(self.trabajador_a.id, ids)
        self.assertNotIn(self.trabajador_b.id, ids)

    #verifica que supervisor a no vea registros de supervisor b
    def test_supervisor_no_ve_registros_de_otra_cuadrilla(self):

        self.client.force_authenticate(self.user_supervisor_a)

        response = self.client.get('/api/registros/')

        self.assertEqual(response.status_code, 200)

        ids = [
            registro['id']
            for registro in response.data['results']
        ]

        self.assertIn(self.registro_a.id, ids)
        self.assertNotIn(self.registro_b.id, ids)

    #verifica que trabajador no pueda crear registros
    def test_trabajador_no_puede_crear_registro(self):

        self.client.force_authenticate(self.user_trabajador)

        response = self.client.post(
            '/api/registros/',
            {
                'trabajador': self.trabajador_a.id,
                'cuartel': self.cuartel_a.id,
                'fecha': '2026-06-04',
                'kilos': 50,
                'horas': 5,
                'calidad': 'Nacional',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 403)

    #verifica que registro duplicado sea rechazado
    def test_registro_duplicado_da_400(self):

        self.client.force_authenticate(self.admin)

        response = self.client.post(
            '/api/registros/',
            {
                'trabajador': self.trabajador_a.id,
                'cuartel': self.cuartel_a.id,
                'fecha': '2026-06-01',
                'kilos': 110,
                'horas': 8,
                'calidad': 'Exportacion',
            },
            format='json'
        )

        self.assertIn(response.status_code, [400, 409])

    #verifica que audit logs sea solo para admin
    def test_audit_logs_solo_admin(self):

        self.client.force_authenticate(self.user_supervisor_a)

        response = self.client.get('/api/audit-logs/')

        self.assertEqual(response.status_code, 403)

    #verifica auditoria real al editar registro
    def test_editar_registro_crea_auditoria_real(self):

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f'/api/registros/{self.registro_a.id}/',
            {
                'kilos': 130,
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        auditoria = AuditLog.objects.filter(
            accion='editar_registro',
            modelo='RegistroCosecha',
            objeto_id=str(self.registro_a.id)
        ).first()

        self.assertIsNotNone(auditoria)
        self.assertIsNotNone(auditoria.datos_previos)
        self.assertIsNotNone(auditoria.datos_nuevos)
