#Res-Tarea-11

##Levantar Backend

###1- Crear entorno virtual

```python -m venv venvsource venv/bin/activate```

###2- Instalar dependencias

```pip install -r requirements.txt```

###3- Configurar archivo .env

Crear un archivo `.env` tomando como referencia `.env.example`.

Ejemplo:

```env
SECRET_KEY=django-clave-secreta
DEBUG=True

DB_NAME=huerto_santa_elena
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

###4- Ejecutar migraciones

```python manage.py migrate```

###5- Cargar datos de prueba

```python manage.py poblar_datos```

###6- Iniciar servidor

```python manage.py runserver```

Backend disponible en:

```http://localhost:8000```

##LEVANTAR EL FRONTEND

###1- Instalar dependencias

```npm install```

###2- Crear archivo .env.local

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

###3- Iniciar aplicación

```npm run dev```

Frontend disponible en:

```http://localhost:3000```

##Credenciales de prueba

###Administrador

```
usuario: admin_huerto
password: admin123
```

###Supervisor

```
usuario: supervisor_norte
password: supervisor123
```

###Trabajador

```
usuario: trabajador_juan
password: trabajador123
```

##Ejecutar pruebas

```python manage.py test```
