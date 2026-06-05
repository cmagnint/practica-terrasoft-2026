# Informe de Evaluación — Tarea 9

**Tarea:** Tarea 9 — Importación masiva de repuestos y análisis de rentabilidad
**Resultado general:** ✅ APROBADA CON OBSERVACIÓN MENOR

---

## Resumen ejecutivo

| Bloque          | Descripción                      | Resultado   | Tests           |
| --------------- | --------------------------------- | ----------- | --------------- |
| 1               | Migraciones y estado inicial      | ✅ PASS     | 4/4             |
| 2               | Datos poblados                    | ✅ PASS     | 5/5             |
| 3               | Archivos Excel de entrada         | ✅ PASS     | 3/3             |
| 4               | Endpoint `/api/repuestos/`      | ✅ PASS     | 5/5             |
| 5               | Primera importación masiva       | ✅ PASS     | 3/3             |
| 6               | Log de errores                    | ✅ PASS     | 3/3             |
| 7               | Idempotencia (segunda ejecución) | ✅ PASS     | 2/2             |
| 8               | Informe de rentabilidad           | ⚠️ PASS\* | 7/8             |
| **TOTAL** |                                   |             | **32/33** |

> \* Un subtest de formato (nombres de hojas sin tildes). El informe funciona correctamente.

---

## Detalle por bloque

### Bloque 1 — Migraciones y estado inicial

| Test                                              | Resultado | Evidencia                       |
| ------------------------------------------------- | --------- | ------------------------------- |
| `manage.py check` sin errores                   | ✅ PASS   | Sin errores de sistema          |
| `manage.py migrate` exitoso                     | ✅ PASS   | Todas las migraciones aplicadas |
| Migración `0005_repuestoorden` aplicada        | ✅ PASS   | Presente y ejecutada            |
| `makemigrations --check` sin cambios pendientes | ✅ PASS   | No hay modelos sin migrar       |

---

### Bloque 2 — Datos poblados

| Test                            | Resultado | Evidencia                    |
| ------------------------------- | --------- | ---------------------------- |
| Mecánicos creados              | ✅ PASS   | 8 mecánicos                 |
| Clientes creados                | ✅ PASS   | 20 clientes                  |
| Vehículos creados              | ✅ PASS   | 35 vehículos                |
| Órdenes creadas                | ✅ PASS   | 60 órdenes (30 completadas) |
| Usuario `admin_taller` existe | ✅ PASS   | Login confirmado             |

---

### Bloque 3 — Archivos Excel de entrada

| Test                                | Resultado | Evidencia                                          |
| ----------------------------------- | --------- | -------------------------------------------------- |
| `repuestos_proveedor_lote_1.xlsx` | ✅ PASS   | 1000 filas, hoja `Repuestos`, columnas correctas |
| `repuestos_proveedor_lote_2.xlsx` | ✅ PASS   | 1000 filas, hoja `Repuestos`, columnas correctas |
| `repuestos_proveedor_lote_3.xlsx` | ✅ PASS   | 1000 filas, hoja `Repuestos`, columnas correctas |

---

### Bloque 4 — Endpoint `/api/repuestos/`

| Test                                                         | Resultado | Evidencia                                                           |
| ------------------------------------------------------------ | --------- | ------------------------------------------------------------------- |
| Login admin → HTTP 200                                      | ✅ PASS   | Token JWT obtenido                                                  |
| POST repuesto válido → HTTP 201 +`costo_total` calculado | ✅ PASS   | `costo_unitario=8500`, `cantidad=2` → `costo_total=17000.00` |
| POST mismo `archivo_origen` + `fila_excel` → HTTP 400   | ✅ PASS   | Idempotencia funciona en endpoint                                   |
| Mecánico GET → HTTP 200                                    | ✅ PASS   | Permiso de lectura correcto                                         |
| Mecánico POST → HTTP 403                                   | ✅ PASS   | Permiso de escritura bloqueado                                      |

---

### Bloque 5 — Primera importación masiva

| Test                       | Resultado | Evidencia                                               |
| -------------------------- | --------- | ------------------------------------------------------- |
| Script ejecuta sin crash   | ✅ PASS   | Salida limpia, sin excepciones                          |
| Conteos por lote correctos | ✅ PASS   | Cada lote: 910 OK / 90 errores                          |
| Total en BD = 2730         | ✅ PASS   | `SELECT COUNT(*) FROM servicio_repuestoorden` → 2730 |

**Detalle por lote:**

| Archivo         | Filas leídas | Importadas OK |    Errores    |
| --------------- | :------------: | :------------: | :-----------: |
| lote_1.xlsx     |      1000      |      910      |      90      |
| lote_2.xlsx     |      1000      |      910      |      90      |
| lote_3.xlsx     |      1000      |      910      |      90      |
| **Total** | **3000** | **2730** | **270** |

---

### Bloque 6 — Log de errores

| Test                                                 | Resultado | Evidencia                                                |
| ---------------------------------------------------- | --------- | -------------------------------------------------------- |
| Archivo `output/errores_importacion.xlsx` generado | ✅ PASS   | Archivo presente                                         |
| Columnas requeridas presentes                        | ✅ PASS   | `archivo_origen, fila_excel, orden_id, motivo, fuente` |
| Distribución de fuentes correcta                    | ✅ PASS   | `api`: 150, `validacion_local`: 120                  |

**Errores por tipo (total 270):**

| Tipo                    | Fuente           | Cantidad esperada | Conteo real |
| ----------------------- | ---------------- | :---------------: | :---------: |
| Orden no Completada     | api              |        90        |     ✅     |
| Orden inexistente       | api              |        60        |     ✅     |
| `costo_unitario` ≤ 0 | validacion_local |        60        |     ✅     |
| `cantidad` ≤ 0       | validacion_local |        60        |     ✅     |

---

### Bloque 7 — Idempotencia

| Test                         | Resultado | Evidencia                     |
| ---------------------------- | --------- | ----------------------------- |
| Segunda ejecución sin crash | ✅ PASS   | Script termina normalmente    |
| Conteo en BD sin cambios     | ✅ PASS   | Antes: 2730 — Después: 2730 |

Segunda corrida: 0 importadas OK, 3000 rechazadas (2730 por duplicado de fila, 270 por errores previos).

---

### Bloque 8 — Informe de rentabilidad

| Test                                                         | Resultado | Evidencia                                 |
| ------------------------------------------------------------ | --------- | ----------------------------------------- |
| Script ejecuta sin crash                                     | ✅ PASS   | Sin excepciones                           |
| Consulta API correctamente (órdenes, repuestos, mecánicos) | ✅ PASS   | 30 órdenes, 2730 repuestos, 8 mecánicos |
| Excel generado en `output/informe_rentabilidad.xlsx`       | ✅ PASS   | Archivo presente                          |
| Excel tiene 3 hojas                                          | ✅ PASS   | Hojas presentes                           |
| Ordenamiento Hoja 1 por margen descendente                   | ✅ PASS   | Correcto                                  |
| Ordenamiento Hoja 2 por margen ascendente                    | ✅ PASS   | Correcto                                  |
| Gráfico en Hoja 1                                           | ✅ PASS   | Gráfico de columnas presente             |
| **Nombres de hojas con tildes**                        | ❌ FAIL   | Ver observación abajo                    |

---

## ❌ Observación menor — Nombres de hojas sin tildes

### Qué falló

Los nombres de las hojas del Excel y algunas columnas no tienen tildes, incumpliendo la especificación exacta de la tarea.

### Diferencia

|         | Especificado en tarea      | Entregado                 |
| ------- | -------------------------- | ------------------------- |
| Hoja 1  | `Resumen por Mecánico`  | `Resumen por Mecanico`  |
| Hoja 2  | `Detalle de Órdenes`    | `Detalle de Ordenes`    |
| Hoja 3  | `Órdenes sin repuestos` | `Ordenes sin repuestos` |
| Columna | `Mecánico`              | `Mecanico`              |
| Columna | `Órdenes`               | `Ordenes`               |

### Dónde corregir

Archivo: `Res-Tarea-9/scripts/generar_informe.py`

Busca los `sheet_name=` y los diccionarios de `rename(columns=...)` y agrega las tildes correspondientes.

### Ejemplo de corrección

```python
# Cambiar esto:
df_resumen.to_excel(writer, sheet_name='Resumen por Mecanico', ...)
df_detalle.to_excel(writer, sheet_name='Detalle de Ordenes', ...)
df_sin_repuestos.to_excel(writer, sheet_name='Ordenes sin repuestos', ...)

# Por esto:
df_resumen.to_excel(writer, sheet_name='Resumen por Mecánico', ...)
df_detalle.to_excel(writer, sheet_name='Detalle de Órdenes', ...)
df_sin_repuestos.to_excel(writer, sheet_name='Órdenes sin repuestos', ...)
```

Lo mismo aplica a los encabezados de columnas en los diccionarios `rename()`:

```python
# Cambiar:
'mecanico_nombre': 'Mecanico',
'ordenes_completadas': 'Ordenes',

# Por:
'mecanico_nombre': 'Mecánico',
'ordenes_completadas': 'Órdenes',
```

---

## ✅ Lo que está bien

- Modelo `RepuestoOrden` implementado correctamente con todos los campos requeridos.
- Constraint de unicidad `(archivo_origen, fila_excel)` funciona y previene duplicados.
- `costo_total` se calcula automáticamente en `save()`.
- Permisos por rol aplicados correctamente en el ViewSet.
- Script de importación valida localmente antes de llamar a la API.
- Log de errores distingue `validacion_local` vs `api` correctamente.
- Idempotencia completa: segunda ejecución no duplica ningún registro.
- Informe de rentabilidad calcula margen bruto y porcentual correctamente.
- Fila `TOTAL` presente en hoja resumen.
- Gráfico comparativo incluido.
- Paginación manejada correctamente en `api_client.py`.
