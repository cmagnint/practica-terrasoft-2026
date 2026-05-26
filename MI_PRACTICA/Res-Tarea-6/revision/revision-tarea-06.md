# 📋 Revisión Día 6 — Django REST Framework con APIView

---

## ✅ Lo que está bien

La estructura general está sólida. Configuración de DRF correcta, logging configurado, todas las views son clases que heredan de `APIView`, el logger está a nivel módulo y cada método lo llama al inicio. Los serializers base están bien — `TemporeroSerializer` con `edad` calculada, `CuartelSerializer` con `cantidad_labores`, `LaborSerializer` con nombres calculados, `LaborCreateSerializer` separado con `validate()` implementado. Las rutas están todas y `.as_view()` en cada una. `pruebas_api.http` con 12 requests existe.

---

## ❌ Lo que debes corregir

### 1. `settings.py` — credenciales hardcodeadas, usar `.env`

Hay valores en `settings.py` que nunca deben estar escritos directamente en el código — si el repo es público, cualquiera puede verlos.

Revisa el archivo completo y encuentra **todos** los valores que deberían vivir en un `.env`. Hay más de uno además de las credenciales de la BD.

> 💡 Pregúntate por cada valor: *¿cambiaría este valor entre mi máquina de desarrollo y un servidor de producción?* Si la respuesta es sí, va al `.env`.

**Lo que debes hacer:**

Instala `python-decouple`:
```bash
pip install python-decouple
```

Agrega al `requirements.txt`.

Crea el archivo `proyecto_django/.env` con los valores que identificaste. Actualiza `settings.py` para leerlos con `config('NOMBRE_VARIABLE')`.

> ⚠️ El archivo `.env` **nunca** se sube al repo. Agrégalo al `.gitignore`.

---

### 3. `TemporeroDetailView` — falta la mitad de la respuesta

Tu view devuelve solo `{"temporero": {...}}`. La spec pide tres secciones:

```python
def get(self, request, rut):
    logger.debug(f"GET {request.path}")
    try:
        temporero = Temporero.objects.get(rut=rut)
    except Temporero.DoesNotExist:
        return Response({'error': f"Temporero con RUT '{rut}' no encontrado"},
                        status=status.HTTP_404_NOT_FOUND)

    # labores_recientes — últimas 10 ordenadas por fecha desc
    labores_recientes = temporero.labores.order_by('-fecha')[:10]

    # stats con aggregate
    from django.db.models import Sum, Count
    stats_qs = temporero.labores.aggregate(
        total_labores=Count('id'),
        total_horas=Sum('horas_trabajadas'),
        total_kilos=Sum('kilos_cosechados'),
    )
    tipos = list(
        temporero.labores.values_list('tipo', flat=True).distinct()
    )

    return Response({
        'temporero': TemporeroSerializer(temporero).data,
        'labores_recientes': LaborSerializer(labores_recientes, many=True).data,
        'stats': {
            'total_labores': stats_qs['total_labores'] or 0,
            'total_horas': float(stats_qs['total_horas'] or 0),
            'total_kilos_cosechados': float(stats_qs['total_kilos'] or 0),
            'tipos_realizados': tipos,
        }
    })
```

---

### 4. `LaborCreateSerializer` — typo en `extra_kwards`

Tienes `extra_kwards` en vez de `extra_kwargs`. Python no lanza error porque simplemente lo ignora como atributo desconocido, pero la configuración extra no se aplica. Corrígelo:

```python
class Meta:
    model = Labor
    fields = [...]
    extra_kwargs = {   # ← con 'g' al final
        ...
    }
```

---

### 5. `logs_anotados.md` — logs sin bytes + bloque markdown sin cerrar

El formato que pide la spec incluye los bytes de la respuesta (el número al final de cada línea del log):

```
"GET /api/temporeros/ HTTP/1.1" 200 4821
                                    ^^^^
                                    bytes devueltos — falta esto
```

Además tienes un bloque de código que no cierra con las tres comillas. Revisa el archivo visualmente — si ves que el resto del documento aparece en color de código, ahí está el bloque sin cerrar.

Para obtener los bytes reales: cuando levantes el servidor y hagas las requests con curl, cópialos directamente del output de la consola. Los bytes son el último número de cada línea del log de `django.server`.

---

## ⚠️ Problemas menores (no bloquean pero corrígelos igual)

**`for` después de `annotate()` — no es un error grave pero hay una forma más limpia:**

Tienes algo así en `ResumenView` y `CuartelDetailView`:

```python
# Lo que tienes
resultado = {}
for item in Labor.objects.values('tipo').annotate(count=Count('id')):
    resultado[item['tipo']] = item['count']
```

Esto está bien — el `for` es sobre un QuerySet ya evaluado, no es N+1. El problema sería si hicieras una query dentro del loop. Lo que tienes no viola la spec, pero puedes simplificarlo con un dict comprehension:

```python
por_tipo = {
    item['tipo']: item['count']
    for item in Labor.objects.values('tipo').annotate(count=Count('id'))
}
```

**`pruebas_api.http` — comentario raro `"201 Created D"`:**

Revisa ese comentario y corrígelo.

---

## 📋 Resumen de cambios

| Archivo | Estado | Cambios requeridos |
|---------|--------|--------------------| 
| `campo/settings.py` | ❌ Fix | Mover credenciales a `.env` con `python-decouple` |
| `.env` | ❌ Crear | Archivo nuevo con credenciales (nunca al repo) |
| `.gitignore` | ❌ Fix | Agregar `.env` |
| `requirements.txt` | ❌ Fix | Agregar `python-decouple` |
| `temporeros/views.py` | ❌ Fix | `TemporeroDetailView`: agregar `labores_recientes` y `stats` |
| `temporeros/serializers.py` | ❌ Fix | Typo `extra_kwards` → `extra_kwargs` |
| `logs_anotados.md` | ❌ Fix | Agregar bytes del log + cerrar bloque markdown |
| `pruebas_api.http` | ⚠️ Fix menor | Limpiar comentario `"201 Created D"` |

---

## ✅ Verificación de endpoints

El servidor levantó correctamente con PostgreSQL en Docker (puerto 5431) y los 9 endpoints respondieron con los códigos correctos:

| Endpoint | Código esperado | Código real |
|----------|-----------------|-------------|
| GET /api/temporeros/ | 200 | ✅ 200 |
| GET /api/temporeros/?supervisor=true | 200 | ✅ 200 |
| GET /api/temporeros/99999999-9/ | 404 JSON | ✅ 404 JSON |
| POST /api/temporeros/ | 405 JSON | ✅ 405 JSON |
| GET /api/labores/?tipo=Cosecha&limite=5 | 200 | ✅ 200 |
| GET /api/cuarteles/A-1/ | 200 | ✅ 200 |
| GET /api/resumen/ | 200 | ✅ 200 |
| POST /api/labores/ sin kilos | 400 con detalle | ✅ 400 con detalle |
| POST /api/labores/ válida | 201 | ✅ 201 |

Los bodies de error son todos JSON — nunca HTML de Django. La API funciona correctamente.

---

## 📤 Entrega

```bash
git add proyecto_django/campo/settings.py
git add proyecto_django/temporeros/views.py
git add proyecto_django/temporeros/serializers.py
git add logs_anotados.md
git add pruebas_api.http
git add requirements.txt
git add .gitignore
# ojo: .env NO se agrega nunca
git commit -m "dia 06 - fix env, detail view y typos"
git push
```