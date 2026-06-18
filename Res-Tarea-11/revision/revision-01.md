# Informe de revisión — Tarea 11 (Huerto Santa Elena)

Revisión de la entrega en `Res-Tarea-11/` contra el enunciado `Tareas/tarea-11.md`.
El informe señala qué está resuelto y qué queda pendiente de corregir. No incluye las
soluciones: el cómo queda de tu parte.

---

## Lo que está resuelto

**Modelado (11.1)**

- Las cuatro entidades más `AuditLog` están completas, con los tipos, `related_name`,
  `on_delete`, `Meta.ordering` e índices que pedía el enunciado.
- El `UniqueConstraint(trabajador, cuartel, fecha)` está bien puesto en el modelo y bajó
  correctamente a la migración (`0001_initial.py`).
- La migración quedó coherente con el modelo.

**Serializers (11.2)**

- Separación lectura/escritura correcta (`RegistroCosechaSerializer` frente a
  `RegistroCosechaCreateSerializer`).
- `total_trabajadores`, `total_cuarteles`, `kilos_acumulados` y `rendimiento` están presentes.
- `kilos_acumulados` usa `aggregate`, no un loop en Python.
- El `validate()` cubre kilos, horas, el caso Descarte y la regla cruzada
  trabajador/cuartel con el mensaje pedido.

**Auth y permisos (11.3)**

- JWT configurado con los tiempos pedidos (30 min / 1 día) e `IsAuthenticated` por defecto.
- `permissions.py` usa una nomenclatura consistente (`es_admin`, `EsAdmin`, …).
- `/api/auth/me/` resuelve el rol por grupo y anida el perfil correcto.

**Visibilidad (11.4)**

- `get_queryset()` por rol está bien planteado en los cuatro ViewSets y usa
  `select_related` en trabajadores, cuarteles y registros.
- Los tres `@action` de métricas (`resumen`, `rendimiento`, `productividad`) usan
  `aggregate`/`annotate`, sin loops en Python.

**Producción (11.6)**

- `/api/health/` público y con los contadores correctos.
- CORS, paginación personalizada (`page_size_query_param`, `max_page_size`) y `python-decouple`
  bien aplicados. `.env.example` sin valores reales y `.env`/`.env.local` en `.gitignore`.

**Datos y frontend (11.7 / 11.10)**

- `poblar_datos` es idempotente (`get_or_create`), respeta la regla cruzada al generar
  registros masivos e imprime un resumen. El `set_password` solo se aplica al crear.
- El frontend conecta de verdad: Server Component que llama a `getHealth()` y maneja el
  caso de API caída sin dejar la pantalla en blanco.

---

## Pendiente — prioritario

### 1. La auditoría de edición no se ejecuta

En `cosecha/views.py` el método está escrito como `perfom_update` (falta una "r"). DRF no
llama a ese método, así que editar un registro no genera ningún `AuditLog`. Es el mismo bug 5
de la Tarea 10 que el enunciado pedía no repetir. Revísalo y piensa cómo lo detectarías con
un test (ver punto 8).

### 2. Faltan permisos de escritura en tres ViewSets

Solo `RegistroCosechaViewSet` implementa `get_permissions()`. `Supervisor`, `Trabajador` y
`Cuartel` no lo tienen. El enunciado (11.4) indica:

- `Supervisor`/`Cuartel`: crear/editar/borrar solo admin.
- `Trabajador`: crear/editar solo admin (un supervisor no crea trabajadores).

Tal como está, el `get_queryset` filtra lo que se ve, pero no bloquea quién puede crear.
¿Qué ocurre si un supervisor o un trabajador hace `POST /api/trabajadores/` o
`POST /api/cuarteles/`? Pruébalo y observa el código de respuesta.

### 3. Auditoría de trabajadores ausente

El enunciado (11.5) pide auditar como mínimo `crear_registro`, `editar_registro`,
`eliminar_registro`, `crear_trabajador` y `desactivar_trabajador`. `TrabajadorViewSet` no
audita nada: faltan dos de las cinco acciones obligatorias.

### 4. Acceso a un registro de otra cuadrilla: revisar el código de respuesta

El enunciado (11.4) pide validar en `get_object()` que un supervisor que accede a un registro
de otra cuadrilla reciba un 403. Como `get_object()` llama a `super().get_object()` y el
`get_queryset` ya viene filtrado, revisa qué código sale cuando el objeto no está en el
queryset del usuario: ¿es 403 o es otro? No hay test ni request en el `.http` que cubra este
caso, así que queda sin verificar.

### 5. El manejo de `DecimalField` no se resolvió ni se documentó

El enunciado (11.2) lo pide de forma explícita: los `DecimalField` se serializan como string
por defecto, el frontend espera números, y hay que decidir y documentar una estrategia
consistente en toda la API. Hoy `kilos`, `horas` y `hectareas` salen como string en los
serializers, pero `rendimiento`, `kilos_acumulados` y los agregados de los `@action` salen
como número. Compara la salida de `/api/registros/` con la de `/api/registros/resumen/`.

---

## Pendiente — funcionalidad incompleta

### 6. Faltan los filtros por query param (11.4)

No están implementados:

- registros: `?trabajador_rut=`, `?cuartel=`, `?calidad=`, `?desde=`, `?hasta=`
- trabajadores: `?supervisor_rut=`, `?activo=`, `?buscar=`

### 7. Filtros de `AuditLogViewSet` ausentes (11.5)

Se piden `?usuario=`, `?accion=`, `?modelo=`, `?desde=`, `?hasta=`. No hay ninguno.

### 8. Los tests no cubren lo que el enunciado exige (11.9)

Hay 10 tests, pero la mayoría solo comprueban `status_code == 200` y no verifican el
comportamiento clave. Faltan, entre otros:

- Request sin token, que debe dar 401.
- Que el supervisor A no vea trabajadores/registros del supervisor B, comprobado por
  dato/contador y no solo por status 200. Es el test central de la tarea.
- Trabajador haciendo `POST` a registros, que debe dar 403.
- Registro duplicado del mismo día, que debe dar 400/409.
- Supervisor editando un registro de otra cuadrilla, que debe dar 403.
- `/api/audit-logs/` accesible solo para admin (otros, 403).
- Que cada edición deje un `AuditLog` con `datos_previos`/`datos_nuevos` correctos. Este test
  habría destapado el bug del punto 1; hoy `test_auditoria_registro` solo crea un `AuditLog`
  a mano y no ejercita el flujo real.

### 9. `resumen` accesible para trabajador

`GET /api/registros/resumen/` debería ser admin/supervisor (11.4), pero `get_permissions()`
no contempla la acción `resumen`, así que cae en el `IsAuthenticated` por defecto. Revisa si
un trabajador autenticado puede llamarla.

### 10. Falta `frontend/campo-web/.env.local.example`

El enunciado (11.10.2) lo pide como entregable. No existe en el repo, aunque la variable sí
está documentada en el README. Además, el `.gitignore` del frontend ignora `.env*`, lo que
taparía ese archivo de ejemplo si lo creas tal cual.

---

## Detalles menores

### 11. Posible N+1 (regla de oro nº5 del proyecto)

- `SupervisorSerializer` hace `obj.trabajadores.count()` y `obj.cuarteles.count()` por fila.
  Al listar supervisores —y al listar trabajadores, porque anida el supervisor completo—
  eso dispara consultas por registro. Mide las queries de `/api/trabajadores/` y
  `/api/supervisores/` (Django Debug Toolbar o `assertNumQueries`) y saca conclusiones.
- `CuartelSerializer.get_kilos_acumulados` hace un `aggregate` por cada cuartel: no es loop en
  Python, pero sí una query por fila al listar. Aplícale el mismo análisis.

### 12. Los `@action` resuelven por id en vez de por `rut`/`nombre`

El enunciado define `/api/trabajadores/<rut>/rendimiento/` y
`/api/cuarteles/<nombre>/productividad/`. La implementación resuelve por el `id` (pk) por
defecto. Funciona, pero no coincide con la ruta pedida.

### 13. README con formato roto

- Los títulos `##Levantar`, `###1-...` no llevan espacio tras los `#`, así que no se renderizan
  como encabezados.
- El comando del entorno virtual está pegado en una sola línea:
  `python -m venv venvsource venv/bin/activate`. Si alguien lo copia, falla.

### 14. Ubicación de `requirements.txt`

El enunciado lo ubica en `backend/requirements.txt`; está en
`backend/proyecto_django/requirements.txt`. Es menor, pero no calza con el árbol de entrega.

### 15. Indentación de comentarios en `views.py`

Algunos comentarios dentro de `RegistroCosechaViewSet` (los de `resumen` y `get_permissions`)
quedaron mal indentados. No rompe nada, pero conviene dejarlo limpio.

### 16. Choices sin tilde

Usaste `'Exportacion'` y el enunciado escribe `Exportación`. Es consistente dentro del código,
así que no es un error; solo tenlo presente como decisión tomada.

---

## Resumen

| Área                        | Estado                                     |
| ---------------------------- | ------------------------------------------ |
| Modelos y migración         | Sólido                                    |
| Serializers                  | Bien, falta resolver Decimals (5)          |
| Auth / JWT / me              | Bien                                       |
| Visibilidad `get_queryset` | Bien                                       |
| Permisos de escritura        | Incompletos (2)                            |
| Auditoría                   | Edición rota (1) y trabajador ausente (3) |
| 403 en `get_object`        | Sin verificar (4)                          |
| Filtros query param          | Faltan (6, 7)                              |
| Tests                        | No cubren lo exigido (8)                   |
| Frontend                     | Conecta; falta `.env.local.example` (10) |
| Documentación y estructura  | Detalles (13, 14)                          |
