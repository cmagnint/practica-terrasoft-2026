# 📘 Tarea 9 — Importación masiva de repuestos desde Excel y análisis de rentabilidad

> **Esta tarea conecta el backend con datos reales en Excel.**
>
> El objetivo es importar repuestos asociados a órdenes de trabajo, validar errores, evitar duplicados y generar un informe de rentabilidad por mecánico.

---

## ⚠️ Estado inicial obligatorio

Esta tarea debe ejecutarse sobre una **base de datos limpia de Tarea 8**.

Los Excel de esta tarea están preparados para una BD limpia generada con `poblar_datos.py`.

Si usas una BD antigua, modificada o con datos de pruebas anteriores, los `orden_id` pueden no coincidir y los resultados esperados no serán confiables.

### Regla para esta tarea

Antes de comenzar:

1. Copia el proyecto de Tarea 8 a `Res-Tarea-9`.
2. Usa una base de datos limpia.
3. Ejecuta migraciones.
4. Ejecuta `poblar_datos.py`.
5. Verifica que exista el usuario `admin_taller`.
6. Verifica que existan órdenes en estado `Completada`.
7. Recién ahí importa los Excel.

---

## 📦 Archivos Excel entregados

Copia estos archivos dentro de:

```txt
Res-Tarea-9/data/
```

Archivos ubicados en Tareas/Tarea-9/lotes:

```txt
repuestos_proveedor_lote_1.xlsx
repuestos_proveedor_lote_2.xlsx
repuestos_proveedor_lote_3.xlsx
```

Cada archivo tiene:

- una hoja llamada `Repuestos`;
- 1000 filas de datos;
- las columnas exactas:

| orden_id | proveedor | detalle | costo_unitario | cantidad |
| -------- | --------- | ------- | -------------: | -------: |

Resumen total:

| Concepto                                         | Cantidad |
| ------------------------------------------------ | -------: |
| Archivos Excel                                   |        3 |
| Filas por archivo                                |     1000 |
| Total filas                                      |     3000 |
| Filas válidas esperadas en primera importación |     2730 |
| Errores intencionales esperados                  |      270 |

Errores intencionales por archivo:

| Tipo de error             | Cantidad por archivo | Fuente esperada   |
| ------------------------- | -------------------: | ----------------- |
| Orden no Completada       |                   30 | API               |
| Orden inexistente         |                   20 | API               |
| `costo_unitario = -500` |                   20 | validación local |
| `cantidad = 0`          |                   20 | validación local |

---

# 🧩 Tarea 9.1 — Modelo `RepuestoOrden` + endpoint

## Objetivo

Crear un modelo para registrar repuestos usados en órdenes de trabajo.

Además, debe ser **idempotente**: si se importa dos veces el mismo archivo y la misma fila, no debe duplicar el registro.

---

## 9.1.1 — Modelo

Archivo:

```txt
proyecto_django/servicio/models.py
```

Agrega el modelo:

```python
from django.core.validators import MinValueValidator

class RepuestoOrden(models.Model):
    """Repuesto utilizado en una orden de trabajo, con su costo de proveedor."""

    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name='repuestos'
    )

    proveedor = models.CharField(max_length=100)
    detalle = models.CharField(max_length=200)

    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)

    archivo_origen = models.CharField(max_length=255)
    fila_excel = models.PositiveIntegerField()

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['archivo_origen', 'fila_excel'],
                name='unique_repuesto_archivo_fila'
            )
        ]

    def save(self, *args, **kwargs):
        self.costo_total = self.costo_unitario * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.archivo_origen}:{self.fila_excel} — Orden #{self.orden_id}"
```

Luego ejecuta:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 9.1.2 — Serializer

Archivo:

```txt
proyecto_django/servicio/serializers.py
```

```python
class RepuestoOrdenSerializer(serializers.ModelSerializer):

    class Meta:
        model = RepuestoOrden
        fields = [
            'id',
            'orden',
            'proveedor',
            'detalle',
            'costo_unitario',
            'cantidad',
            'costo_total',
            'archivo_origen',
            'fila_excel',
            'creado_en',
        ]
        read_only_fields = ['costo_total', 'creado_en']

    def validate_costo_unitario(self, value):
        if value <= 0:
            raise serializers.ValidationError("El costo unitario debe ser mayor a 0.")
        return value

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value

    def validate_orden(self, value):
        if value.estado != 'Completada':
            raise serializers.ValidationError(
                "Solo se pueden registrar repuestos en órdenes Completadas."
            )
        return value

    def validate(self, attrs):
        archivo_origen = attrs.get('archivo_origen')
        fila_excel = attrs.get('fila_excel')

        if archivo_origen and fila_excel:
            existe = RepuestoOrden.objects.filter(
                archivo_origen=archivo_origen,
                fila_excel=fila_excel
            ).exists()

            if existe:
                raise serializers.ValidationError(
                    "Esta fila del archivo ya fue importada anteriormente."
                )

        return attrs
```

---

## 9.1.3 — ViewSet y permisos

Archivo:

```txt
proyecto_django/servicio/views.py
```

Usa los permisos reales del repo:

```python
class RepuestoOrdenViewSet(viewsets.ModelViewSet):
    """
    Gestiona repuestos asociados a órdenes de trabajo.
    - Solo administrador puede crear, editar y eliminar.
    - Administrador y mecánico pueden ver.
    """
    serializer_class = RepuestoOrdenSerializer

    def get_queryset(self):
        qs = RepuestoOrden.objects.select_related('orden')

        orden_id = self.request.query_params.get('orden_id')
        if orden_id:
            qs = qs.filter(orden_id=orden_id)

        return qs.order_by('id')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrador()]
        return [EsAdministradorOMecanico()]
```

> Importante: no uses `IsAdmin` ni `IsAdminOrMecanico` si esos permisos no existen en el repo.
> Debes usar los permisos reales: `EsAdministrador` y `EsAdministradorOMecanico`.

---

## 9.1.4 — Registrar endpoint

Archivo:

```txt
proyecto_django/servicio/urls.py
```

```python
router.register('repuestos', views.RepuestoOrdenViewSet, basename='repuesto')
```

Endpoint esperado:

```txt
/api/repuestos/
```

---

## 9.1.5 — Prueba manual del endpoint

Ejemplo:

```json
{
    "orden": 26,
    "proveedor": "AutoParts SpA",
    "detalle": "Filtro de aceite prueba",
    "costo_unitario": 8500,
    "cantidad": 2,
    "archivo_origen": "prueba_manual.xlsx",
    "fila_excel": 2
}
```

Resultado esperado:

```json
{
    "costo_total": "17000.00"
}
```

Si envías nuevamente el mismo `archivo_origen` y la misma `fila_excel`, debe devolver error y no duplicar.

---

# 🧩 Tarea 9.2 — Importación masiva desde 3 Excel

## Objetivo

Crear un script Python que lea los 3 Excel, valide cada fila y envíe las filas válidas a la API.

---

## 9.2.1 — Estructura esperada

```txt
Res-Tarea-9/
├── data/
│   ├── repuestos_proveedor_lote_1.xlsx
│   ├── repuestos_proveedor_lote_2.xlsx
│   └── repuestos_proveedor_lote_3.xlsx
├── scripts/
│   ├── api_client.py
│   ├── importar_repuestos.py
│   └── generar_informe.py
├── output/
└── README.md
```

---

## 9.2.2 — Dependencias

Asegúrate de tener estas dependencias:

```txt
pandas
requests
openpyxl
```

Puedes instalarlas con:

```bash
pip install pandas requests openpyxl
```

Si el proyecto usa `requirements.txt`, agrégalas ahí.

---

## 9.2.3 — Módulo compartido `api_client.py`

Archivo:

```txt
Res-Tarea-9/scripts/api_client.py
```

```python
import requests

API_BASE = 'http://localhost:8000/api'

CREDENCIALES = {
    'username': 'admin_taller',
    'password': 'admin123',
}


def obtener_token():
    url = f'{API_BASE}/auth/login/'
    response = requests.post(url, json=CREDENCIALES)

    if response.status_code != 200:
        raise Exception(f'Error al autenticar: {response.status_code} - {response.text}')

    return response.json()['access']


def extraer_resultados(data):
    """
    Soporta distintos formatos de respuesta:
    - DRF paginado: {"results": [...]}
    - Wrapper del repo: {"ordenes": [...]}
    - Wrapper del repo: {"mecanicos": [...]}
    - Wrapper del repo: {"repuestos": [...]}
    - Lista directa: [...]
    """
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    if 'results' in data:
        return data['results']

    for key in ['ordenes', 'mecanicos', 'repuestos']:
        if key in data:
            return data[key]

    return []


def obtener_todos(endpoint, headers, params=None):
    resultados = []
    url = f'{API_BASE}/{endpoint}'

    while url:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f'Error GET {url}: {response.status_code} - {response.text}')

        data = response.json()
        resultados.extend(extraer_resultados(data))

        if isinstance(data, dict):
            url = data.get('next')
        else:
            url = None

        params = None

    return resultados
```

---

## 9.2.4 — Script `importar_repuestos.py`

Archivo:

```txt
Res-Tarea-9/scripts/importar_repuestos.py
```

El script debe:

1. Autenticarse con la API.
2. Buscar los 3 Excel en `../data/`.
3. Leer la hoja `Repuestos`.
4. Validar cada fila localmente.
5. Enviar cada fila válida a `POST /api/repuestos/`.
6. Enviar también:
   - `archivo_origen`
   - `fila_excel`
7. Acumular exitosos y errores.
8. Guardar un log en `../output/errores_importacion.xlsx`.
9. Imprimir resumen por archivo.
10. Imprimir resumen general.

---

## 9.2.5 — Archivos a recorrer

No hardcodees una sola ruta.

Usa algo similar a:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'

EXCEL_FILES = sorted(DATA_DIR.glob('repuestos_proveedor_lote_*.xlsx'))
```

---

## 9.2.6 — Validaciones locales

Antes de llamar a la API, valida:

- columnas requeridas;
- `orden_id` entero;
- `proveedor` no vacío;
- `detalle` no vacío;
- `costo_unitario > 0`;
- `cantidad > 0`.

Columnas requeridas:

```python
COLUMNAS_REQUERIDAS = [
    'orden_id',
    'proveedor',
    'detalle',
    'costo_unitario',
    'cantidad',
]
```

---

## 9.2.7 — Payload enviado a la API

Cada fila válida debe enviarse así:

```python
payload = {
    'orden': int(fila['orden_id']),
    'proveedor': str(fila['proveedor']).strip(),
    'detalle': str(fila['detalle']).strip(),
    'costo_unitario': float(fila['costo_unitario']),
    'cantidad': int(fila['cantidad']),
    'archivo_origen': archivo_path.name,
    'fila_excel': fila_excel,
}
```

Donde:

```python
fila_excel = idx + 2
```

Porque la fila 1 corresponde a los encabezados de Excel.

---

## 9.2.8 — Log de errores

Archivo generado:

```txt
Res-Tarea-9/output/errores_importacion.xlsx
```

Debe incluir como mínimo:

| archivo_origen | fila_excel | orden_id | proveedor | detalle | costo_unitario | cantidad | motivo | fuente |
| -------------- | ---------: | -------: | --------- | ------- | -------------: | -------: | ------ | ------ |

Valores posibles para `fuente`:

```txt
validacion_local
api
```

---

## 9.2.9 — Resultado esperado en primera ejecución

```txt
========================================
IMPORTACIÓN DE REPUESTOS POR LOTES
========================================

Procesando archivo: repuestos_proveedor_lote_1.xlsx
Filas leídas:        1000
Importadas OK:        910
Errores:               90

Procesando archivo: repuestos_proveedor_lote_2.xlsx
Filas leídas:        1000
Importadas OK:        910
Errores:               90

Procesando archivo: repuestos_proveedor_lote_3.xlsx
Filas leídas:        1000
Importadas OK:        910
Errores:               90

========================================
RESULTADO GENERAL
========================================
Total archivos:       3
Total filas leídas:   3000
Importadas OK:        2730
Errores:              270

Log de errores guardado en:
../output/errores_importacion.xlsx
========================================
```

---

## 9.2.10 — Resultado esperado en segunda ejecución

Si corres el script por segunda vez sin limpiar la BD:

- No debe crashear.
- No debe duplicar registros.
- Las filas ya importadas deben ser rechazadas por la API.
- El log tendrá muchos más errores porque los 2730 registros válidos ya existen.

Esto es correcto.

Lo importante es que la cantidad de registros en la base no aumente en la segunda ejecución.

---

# 🧩 Tarea 9.3 — Informe de rentabilidad

## Objetivo

Crear un script que consulte la API, cruce órdenes, repuestos y mecánicos, y genere un reporte Excel.

---

## 9.3.1 — Script `generar_informe.py`

Archivo:

```txt
Res-Tarea-9/scripts/generar_informe.py
```

Debe:

1. Autenticarse con la API.
2. Obtener:
   - órdenes completadas;
   - repuestos;
   - mecánicos.
3. Manejar respuestas paginadas o con wrappers personalizados.
4. Construir DataFrames.
5. Calcular rentabilidad.
6. Imprimir resumen en consola.
7. Generar un Excel de salida.

---

## 9.3.2 — Endpoints a consultar

```txt
GET /api/ordenes/?estado=Completada
GET /api/repuestos/
GET /api/mecanicos/
```

Usa `obtener_todos()` desde `api_client.py`.

---

## 9.3.3 — Métricas por mecánico

| Métrica                | Fórmula                                                           |
| ----------------------- | ------------------------------------------------------------------ |
| `ordenes_completadas` | cantidad de órdenes completadas del mecánico                     |
| `monto_facturado`     | suma de `orden.monto`                                            |
| `costo_repuestos`     | suma de `repuesto.costo_total` asociado a órdenes del mecánico |
| `margen_bruto`        | `monto_facturado - costo_repuestos`                              |
| `margen_pct`          | `margen_bruto / monto_facturado * 100`                           |

---

## 9.3.4 — Excel de reporte

Archivo generado:

```txt
Res-Tarea-9/output/informe_rentabilidad.xlsx
```

Debe tener 3 hojas.

---

### Hoja 1 — `Resumen por Mecánico`

Columnas:

| Mecánico | Especialidad | Órdenes | Monto Facturado | Costo Repuestos | Margen Bruto | Margen % |
| --------- | ------------ | -------: | --------------: | --------------: | -----------: | -------: |

Reglas:

- Ordenar por `Margen %` descendente.
- Incluir fila de totales.
- Formato moneda en montos.
- Formato porcentaje en margen.
- Agregar gráfico de barras comparando:
  - `Monto Facturado`
  - `Costo Repuestos`

---

### Hoja 2 — `Detalle de Órdenes`

Columnas:

| Orden ID | Mecánico | Vehículo | Fecha | Monto | Costo Repuestos | Margen | Margen % |
| -------- | --------- | --------- | ----- | ----: | --------------: | -----: | -------: |

Reglas:

- Una fila por orden completada.
- Ordenar por `Margen %` ascendente.
- Las órdenes menos rentables deben aparecer primero.

---

### Hoja 3 — `Órdenes sin repuestos`

Columnas:

| Orden ID | Mecánico | Vehículo | Fecha | Monto |
| -------- | --------- | --------- | ----- | ----: |

Si no hay órdenes sin repuestos, la hoja debe existir igual y mostrar:

```txt
Todas las órdenes tienen repuestos registrados
```

---

## 9.3.5 — Salida esperada en consola

```txt
========================================
INFORME DE RENTABILIDAD — Taller AutoServicio
Generado: 2026-06-02 12:00
========================================

RESUMEN POR MECÁNICO
--------------------------------------------
Mecánico              Órdenes  Monto        Costo        Margen      Margen%
Carlos Muñoz          12       $1.800.000   $980.000     $820.000    45,6%
Ana López              8       $950.000     $610.000     $340.000    35,8%
Pedro Soto             5       $480.000     $340.000     $140.000    29,2%
--------------------------------------------
TOTAL                 25       $3.230.000   $1.930.000   $1.300.000  40,2%

ALERTAS
--------------------------------------------
⚠️  6 órdenes completadas sin repuestos registrados.
⚠️  3 mecánicos con margen menor al 25%.

========================================
Informe guardado en: ../output/informe_rentabilidad.xlsx
========================================
```

Los nombres y montos pueden variar según los datos de tu API, pero el formato general debe respetarse.

---

# 📤 Entrega final esperada

```txt
Res-Tarea-9/
├── data/
│   ├── repuestos_proveedor_lote_1.xlsx
│   ├── repuestos_proveedor_lote_2.xlsx
│   └── repuestos_proveedor_lote_3.xlsx
├── scripts/
│   ├── api_client.py
│   ├── importar_repuestos.py
│   └── generar_informe.py
├── output/
│   ├── errores_importacion.xlsx
│   └── informe_rentabilidad.xlsx
└── README.md
```

En Django:

```txt
proyecto_django/servicio/
├── models.py
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

---

# 🧪 Evaluación rápida

Para considerar la tarea correcta:

1. La BD parte limpia.
2. Los 3 Excel se procesan.
3. La primera importación da aproximadamente:
   - 2730 importadas;
   - 270 errores.
4. La segunda importación no duplica.
5. Se genera `errores_importacion.xlsx`.
6. Se genera `informe_rentabilidad.xlsx`.
7. El informe tiene 3 hojas.
8. El reporte muestra rentabilidad por mecánico.
