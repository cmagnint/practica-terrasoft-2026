# Res-Tarea-11

## Levantar Backend

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r backend/requirements.txt
```

### 3. Configurar archivo .env

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

### 4. Ejecutar migraciones

```bash
python manage.py migrate
```

### 5. Cargar datos de prueba

```bash
python manage.py poblar_datos
```

### 6. Iniciar servidor

```bash
python manage.py runserver
```

Backend disponible en:

```text
http://localhost:8000
```


## Levantar Frontend

### 1. Instalar dependencias

```bash
npm install
```

### 2. Crear archivo .env.local

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

### 3. Iniciar aplicación

```bash
npm run dev
```

Frontend disponible en:

```text
http://localhost:3000
```


## Credenciales de prueba

### Administrador

```text
usuario: admin_huerto
password: admin123
```

### Supervisor

```text
usuario: supervisor_norte
password: supervisor123
```

### Trabajador

```text
usuario: trabajador_juan
password: trabajador123
```


## Ejecutar pruebas

```bash
python manage.py test
```

## Criterio sobre campos decimales

En esta API se mantiene el comportamiento por defecto de Django REST Framework para los campos `DecimalField`.
Por eso campos como `kilos`, `horas` y `hectareas` pueden aparecer como texto en las respuestas JSON, por ejemplo:

```json
"kilos": "120.50"
```