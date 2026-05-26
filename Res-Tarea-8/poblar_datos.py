import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_DIR = os.path.join(BASE_DIR, 'proyecto_django')
sys.path.append(PROYECTO_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller.settings')

import django
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User, Group
from servicio.models import Mecanico, Cliente

#este call llama al poblar_datos que esta en la ruta commands/
call_command('poblar_datos')

#grupos
admin_group, _ = Group.objects.get_or_create(name='admin')
mecanico_group, _ = Group.objects.get_or_create(name='mecanico')
cliente_group, _ = Group.objects.get_or_create(name='cliente')

#usuarios
admin_user, _ = User.objects.get_or_create(username='admin_taller')
admin_user.set_password('admin123')
admin_user.is_staff = True
admin_user.save()
admin_user.groups.add(admin_group)

mec_user, _ = User.objects.get_or_create(username='carlos_munoz')
mec_user.set_password('mecanico123')
mec_user.save()
mec_user.groups.add(mecanico_group)

cli_user, _ = User.objects.get_or_create(username='juan_perez')
cli_user.set_password('cliente123')
cli_user.save()
cli_user.groups.add(cliente_group)

#vinculos
Mecanico.objects.filter(rut='11111111-1').update(usuario=mec_user)
Cliente.objects.filter(rut='10111111-1').update(usuario=cli_user)

print("OK: datos + usuarios creados correctamente")
