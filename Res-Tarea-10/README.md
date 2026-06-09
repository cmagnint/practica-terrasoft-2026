#1. Res-Tarea-9 - API Taller Mecánico

#2. Como levantar el proyecto desde cero

##2.1 Clonar el repositorio

Descargar el repositorio desde GitHub:

```git clone <url-repositorio>

   cd Res-Tarea-9```

El primer comando descarga el proyecto
El segundo comando ingresa a la carpeta principal

##2.2 Crear entorno virtual

Crear entorno virtual:

```python -m venv venv```

Activar entorno virtual:

```source venv/bin/activate```

Instalar dependencias:

```pip install -r requirements.txt```

##2.3 Preparar PostgreSQL

Si PostgreSQL se encuentra ejecutndose dentro de Docker:

```docker start postgres-taller```

Verificar que el contenedor quede ejecutandose antes de iniciar Django

##2.4 Crear archivo .env

Crear un archivo `.env` en la raíz del proyecto:

```env
DB_NAME=taller_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=django-secret-key
DEBUG=True
```

##2.5 Ejecutar migraciones

Ingresar al proyecto Django:

```cd proyecto_django```

Crear migraciones:

```python manage.py makemigrations```

Aplicar migraciones:

```python manage.py migrate```

##2.6 Poblar datos de prueba

Ejecutar:

```python manage.py poblar_datos```

Este comando crea automticamente:

1. Usuarios
2. Clientes
3. Mecanicos
4. Vehiculos
5. Ordenes de trabajo

##2.7 Ejecutar servidor

```python manage.py runserver```

La API quedara disponible en:

```http://127.0.0.1:8000/```

#3. Usuarios de prueba

##Administrador

```
username: admin_taller
password: admin123
```
Permisos:

1. Acceso total al sistema
2. Administracion completa
3. Acceso a auditoria

##Mecanico

```
username: carlos_munoz
password: mecanico123
```
Permisos:

1. Visualizar ordenes asignadas
2. Completar ordenes
3. Consultar clientes relacionados

##Cliente

```
username: juan_perez
password: cliente123
```
Permisos:

1. Ver sus vehiculos
2. Ver sus ordenes
3. Consultar informacion propia

#4. Autenticacion JWT

La API utiliza JSON Web Token

Proceso:

1. Usuario envia username y password
2. Django valida crednciales
3. Se genera token JWT
4. El token se utiliza en peticiones protegidas

##Obtener token

Endpoint:

```http://POST /api/auth/login/```

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

##Utilizar token
```http://Authorization: Bearer TOKEN_ACCESS
```

##Usuario autenticado

```http://GET /api/auth/me/
```

Devuelve informacion del usuario autenticado y su rol

#5. Endpoints principales

| Endpoint                     | Método | Descripción         |
| ---------------------------- | ------ | ------------------- |
| /api/auth/login/             | POST   | Genera token JWT    |
| /api/auth/refresh/           | POST   | Renueva token       |
| /api/auth/verify/            | POST   | Verifica token      |
| /api/auth/me/                | GET    | Usuario autenticado |
| /api/mecanicos/              | GET    | Lista mecánicos     |
| /api/clientes/               | GET    | Lista clientes      |
| /api/vehiculos/              | GET    | Lista vehículos     |
| /api/ordenes/                | GET    | Lista órdenes       |
| /api/repuestos/              | GET    | Lista repuestos     |
| /api/ordenes/{id}/completar/ | POST   | Completa orden      |
| /api/ordenes/{id}/cancelar/  | POST   | Cancela orden       |
| /api/audit-logs/             | GET    | Consulta auditoría  |


#6. Auditoria

El sistema registra automaticamente acciones relevantes realizadas por los usuarios

Ejemplos:

1. Crear cliente
2. Actualizar cliente
3. Crear vehículo
4. Crear orden
5. Completar orden
6. Cancelar orden
7. Desactivar mecánico

Solo administradores tienen acceso

#7. Importación masiva de repuestos

La Tarea 9 incorpora un proceso de importacion masiva desde archivos Excel

Los archivos deben ubicarse dentro de:

```Res-Tarea-9/data/```

Ejemplo:

```
data/
├── repuestos_proveedor_lote_1.xlsx
├── repuestos_proveedor_lote_2.xlsx
└── repuestos_proveedor_lote_3.xlsx
```

##Ejecutar importacion

Desde la raíz del proyecto:

```python scripts/importar_repuestos.py```

El proceso realiza:

1. Lectura de archivos Excel
2. Validación de columnas
3. Validación de datos
4. Consumo de API mediante JWT
5. Registro de errores

##Resultado de importación

Se genera:

```
output/errores_importacion.xlsx
```

El archivo contiene:

1. Archivo origen
2. Fila del Excel
3. Datos originales
4. Motivo del error

La importacion es idempotente, por lo que una segunda ejecucion no genera registros duplicados

#8. Informe de rentabilidad

El proyecto incorpora un modulo de analisis para generar reportes de rentabilidad

##Ejecutar informe

Desde la raiz del proyecto:

```python scripts/generar_informe.py```

El script consulta:

1. Ordenes completadas
2. Repuestos importados
3. Mecánicos registrados

## Metricas calculadas

1. Facturación por mecánico
2. Costos de repuestos
3. Margen bruto
4. Margen porcentual
5. Ordenes sin repuestos

##Resultado

Se genera:

```output/informe_rentabilidad.xlsx```

##Hojas generadas

###Resumen por Mecánico

Contiene:

1. Mecánico
2. Especialidad
3. Cantidad de órdenes
4. Facturación
5. Costos
6. Margen bruto
7. Margen %

###Detalle de Órdenes

Contiene:

1. ID de orden
2. Mecánico
3. Vehículo
4. Fecha
5. Facturación
6. Costos
7. Margen

###Ordenes sin repuestos

Muestra ordenes completadas que no poseen repuestos registrados

##Grafico

El informe incluye un gráfico comparativo entre:

1. Monto facturado
2. Costo de repuestos

#9. Documentacion de la API

## Swagger UI

```http://127.0.0.1:8000/api/docs/```
##Redoc

```http://127.0.0.1:8000/api/redoc/```
##OpenAPI Schema

```http://127.0.0.1:8000/api/schema/```
