import os
import sys

from django.contrib.auth.models import User

#agrega proyecto_django al path de python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROYECTO_DIR = os.path.join(
    BASE_DIR,
    'proyecto_django'
)

sys.path.append(PROYECTO_DIR)

#configuracion django
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'taller.settings'
)

import django
django.setup()

#permite ejecutar comandos django desde python
from django.core.management import call_command


#ejecuta el comando poblar_datos
call_command('poblar_datos')

#usuarios de prueba para autenticación JWT
admin_user, _ = User.objects.get_or_create(
    username='admin_taller',
    defaults={
        'email': 'admin@taller.cl',
        'is_staff': True,
        'is_superuser': True
    }
)

#set_password guarda contraseña encriptada
admin_user.set_password('admin123')
admin_user.save()


mec_user, _ = User.objects.get_or_create(
    username='carlos_munoz',
    defaults={
        'email': 'carlos@taller.cl'
    }
)

mec_user.set_password('mecanico123')
mec_user.save()


cli_user, _ = User.objects.get_or_create(
    username='juan_perez',
    defaults={
        'email': 'juan@gmail.com'
    }
)

cli_user.set_password('cliente123')
cli_user.save()


print("Usuarios de prueba creados correctamente")
