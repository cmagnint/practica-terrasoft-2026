import os
import sys

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
