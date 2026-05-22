###====================================================================================================
###1- Como levantar el proyecto desde 0
###====================================================================================================
Primeramente clonamos el repositorio
Con el siguiente comando se descarga el proyecto desde GitHub a tu dispositivo

git clone <url-repositorio>
cd Res-Tarea-8 >con este comando entramos a la carpeta donde se ubica el proyecto

###1.2 Crear entorno virtual
El entorno virtual permite instalar librerias Python sin afectar otros proyectos

python -m venv venv
source venv/bin/activate

Luego, con este comando instala todas las librerias necesarias del proyecto

pip install -r requirements.txt

###1.3 Levantar PostgreSQL Docker

El proyecto utiliza PostgreSQL dentro de Docker para manejar la base de datos

docker start postgres-taller

###Creamos un archivo .env
El archivo .env guarda configuraciones sensibles del proyecto

Crear archivo .env en la raiz del proyecto (Res-Tarea-8):
DB_NAME=taller_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=django-secret-key
DEBUG=True

###1.4 Ejecutar migraciones
Las migraciones crean las tablas necesarias en PostgreSQL

Entrar carpeta proyecto:

cd proyecto_django

Ejecutamos:

python manage.py makemigrations
python manage.py migrate
Poblar datos iniciales

Estos comandos crean:

mecanicos
clientes
vehiculos
ordenes
usuarios de prueba
python manage.py poblar_datos

###1.5 Ejecutar servidor
Este comando inicia el servidor Django local

python manage.py runserver

Servidor disponible en un localhost:
http://127.0.0.1:8000/

###====================================================================================================
###2- Credenciales de los 3 usuarios de prueba
###====================================================================================================

###2.1 El sistema tiene 3 tipos de usuarios:

-administrador
-mecanico
-cliente

Administrador, el cual tiene acceso completo al sistema

username: admin
password: admin123

Mecanico, el cual puede gestionar ordenes asignadas a el

username: mecanico1
password: mecanico123

Cliente, el cual puede visualizar solo sus propios datos

username: cliente1
password: cliente123

###====================================================================================================
###3 Como loguearse y usar el token
###====================================================================================================
El sistema usa JWT Authentication

JWT funciona funciona de la siguiente manera:

el usuario envia username y password
Django valida credenciales
la API devuelve un token
el token se envia en cada request protegida

###3.1 Obtener token JWT
curl -X POST http://127.0.0.1:8000/api/token/ \
-H "Content-Type: application/json" \
-d '{
    "username": "admin",
    "password": "admin123"
}'

Respuesta ejemplo:

{
    "refresh": "TOKEN_REFRESH",
    "access": "TOKEN_ACCESS"
}


###3.2 Usar token Bearer

El token access se envia usando Authorization Bearer

curl http://127.0.0.1:8000/api/ordenes/ \
-H "Authorization: Bearer TOKEN_ACCESS"

###====================================================================================================
###4 - Tabla de endpoints principales y roles
###====================================================================================================
Endpoint			Metodo	Rol permitido		Explicacion
/api/token/			POST	Publico			Genera token JWT
/api/auth/me/			GET	Usuarios autenticados	Devuelve informacion usuario logueado
/api/mecanicos/			GET	Admin			Lista mecanicos
/api/clientes/			GET	Admin			Lista clientes
/api/vehiculos/			GET	Admin/Cliente		Lista vehiculos
/api/ordenes/			GET	Admin/Mecanico		Lista ordenes
/api/ordenes/{id}/completar/	POST	Admin/Mecanico		Completa orden
/api/ordenes/{id}/cancelar/	POST	Admin			Cancela orden
/api/audit-logs/		GET	Admin			Consulta auditoria sistema

###====================================================================================================
###5-Link documentacion interactiva Swagger
###====================================================================================================

Swagger genera documentacion automatica de la API
Permite:

ver endpoints
probar requests
revisar respuestas JSON
revisar autenticacion JWT

Swagger UI:
http://127.0.0.1:8000/api/docs/

Schema OpenAPI:
http://127.0.0.1:8000/api/schema/
