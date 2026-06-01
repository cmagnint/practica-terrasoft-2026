# Res-Tarea-8 - API Taller Mecanico

# 1. Como levantar el proyecto desde cero

A continuacion se explican todos los pasos necesarios para ejecutar el proyecto en un computador nuevo.

## 1.1 Clonar el repositorio

Primero debemos descargar el proyecto desde GitHub.

```bash
git clone <url-repositorio>
cd Res-Tarea-8
```

El primer comando descarga el repositorio.

El segundo comando nos mueve a la carpeta principal del proyecto.


## 1.2 Crear un entorno virtual

Python permite crear entornos virtuales para instalar librerias sin afectar otros proyectos.

Crear entorno virtual:

```bash
python -m venv venv
```

Activar entorno virtual:

```bash
source venv/bin/activate
```

Una vez activado, instalamos todas las dependencias necesarias:

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene todas las librerias utilizadas por el proyecto.


## 1.3 Preparar la base de datos PostgreSQL

Este proyecto utiliza PostgreSQL como sistema de base de datos.

Si PostgreSQL se encuentra dentro de Docker:

```bash
docker start postgres-taller
```

Este comando inicia el contenedor que contiene la base de datos.


## 1.4 Crear archivo .env

El archivo `.env` permite guardar configuraciones sensibles fuera del codigo fuente.

Crear un archivo llamado `.env` en la raiz del proyecto con el siguiente contenido:

```env
DB_NAME=taller_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=django-secret-key
DEBUG=True
```

Estos datos son utilizados por Django para conectarse a PostgreSQL.

## 1.5 Ejecutar migraciones

Las migraciones son archivos que crean las tablas necesarias dentro de la base de datos.

Ingresar a la carpeta del proyecto Django:

```bash
cd proyecto_django
```

Ejecutar:

```bash
python manage.py makemigrations
python manage.py migrate
```

Con estos comandos se crean todas las tablas definidas en los modelos.


## 1.6 Poblar datos de prueba

Para facilitar las pruebas del sistema existe un comando que genera informacion automaticamente.

Ejecutar:

```bash
python manage.py poblar_datos
```

Este comando crea:

Usuarios de prueba
Clientes
Mecanicos
Vehiculos
Ordenes de trabajo

De esta manera no es necesario ingresar todos los datos manualmente.

## 1.7 Ejecutar el servidor

Una vez configurado todo lo anterior, se puede iniciar el servidor.

```bash
python manage.py runserver
```

La API quedara disponible en:

```text
http://127.0.0.1:8000/
```
# 2. Usuarios de prueba

El sistema crea automaticamente tres tipos de usuarios para probar los distintos permisos.

## Administrador

El administrador tiene acceso completo al sistema.

```text
username: admin_taller
password: admin123
```
Puede:

Ver todos los clientes
Ver todos los vehiculos
Ver todas las ordenes
Revisar auditoria
Crear y modificar registros

## Mecanico

Representa a un trabajador del taller.

```text
username: carlos_munoz
password: mecanico123
```

Puede:

Ver ordenes asignadas a el
Completar ordenes
Cancelar ordenes
Ver clientes relacionados a sus ordenes

No puede acceder a la auditoria ni administrar usuarios.


## Cliente

Representa al dueño de uno o mas vehiculos.

```text
username: juan_perez
password: cliente123
```

Puede:

Ver sus vehiculos
Ver sus ordenes
Consultar informacion propia

No puede crear ordenes ni modificar informacion administrativa.

# 3. Autenticacion JWT

La API utiliza JWT (JSON Web Token).

Este mecanismo permite autenticar usuarios sin mantener sesiones en el servidor.

1. El usuario envia username y password.
2. Django valida las credenciales.
3. El sistema genera un token.
4. El token se utiliza en todas las peticiones protegidas.


## Obtener token

Enviar una peticion a:

```http
POST /api/auth/login/
```

Ejemplo:

```json
{
  "username": "admin_taller",
  "password": "admin123"
}
```

Respuesta:

```json
{
  "refresh": "...",
  "access": "..."
}
```

## Utilizar token

Una vez obtenido el token access, este debe enviarse en el encabezado Authorization.

Ejemplo:

```http
Authorization: Bearer TOKEN_ACCESS
```

## Consultar usuario autenticado

Endpoint:

```http
GET /api/auth/me/
```

Este endpoint devuelve informacion del usuario autenticado y el rol que posee dentro del sistema.

# 4. Endpoints principales

| Endpoint                     | Metodo | Descripcion                  |
| ---------------------------- | ------ | ---------------------------- |
| /api/auth/login/             | POST   | Genera token JWT             |
| /api/auth/refresh/           | POST   | Renueva token                |
| /api/auth/verify/            | POST   | Verifica token               |
| /api/auth/me/                | GET    | Devuelve usuario autenticado |
| /api/mecanicos/              | GET    | Lista mecanicos              |
| /api/clientes/               | GET    | Lista clientes               |
| /api/vehiculos/              | GET    | Lista vehiculos              |
| /api/ordenes/                | GET    | Lista ordenes                |
| /api/ordenes/{id}/completar/ | POST   | Completa una orden           |
| /api/ordenes/{id}/cancelar/  | POST   | Cancela una orden            |
| /api/audit-logs/             | GET    | Consulta auditoria           |

# 5. Auditoria

El sistema registra automaticamente acciones importantes realizadas por los usuarios.

Algunos ejemplos son:

Crear clientes
Actualizar clientes
Crear vehiculos
Crear ordenes
Completar ordenes
Cancelar ordenes
Desactivar mecanicos

Estos registros permiten mantener trazabilidad sobre las acciones realizadas dentro del sistema.

La auditoria puede consultarse mediante:

```text
/api/audit-logs/
```

Solo los administradores tienen acceso a esta informacion.

# 6. Documentacion de la API

La API genera documentacion automaticamente mediante OpenAPI y drf-spectacular.

Esto permite revisar todos los endpoints sin necesidad de leer el codigo fuente.

## Swagger UI

Interfaz interactiva para probar endpoints directamente desde el navegador.

```text
http://127.0.0.1:8000/api/docs/
```

## ReDoc

Version alternativa de la documentacion con un formato mas orientado a lectura.

```text
http://127.0.0.1:8000/api/redoc/
```

## OpenAPI Schema

Archivo JSON utilizado para describir formalmente toda la API.

```text
http://127.0.0.1:8000/api/schema/
```

