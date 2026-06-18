# Informe de revisión — Tarea 11 (Huerto Santa Elena)

Revisión de la entrega en `Res-Tarea-11/` contra el enunciado `Tareas/tarea-11.md`.
El informe señala qué está resuelto y qué queda pendiente de corregir, con una indicación
breve de la dirección de la corrección. No incluye la solución completa.

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
llama a ese método, por lo que editar un registro no genera ningún `AuditLog`. Es el mismo
bug 5 de la Tarea 10 que el enunciado pedía no repetir.
Dirección: el nombre del método debe coincidir con el hook que DRF invoca en la edición.

### 2. Faltan permisos de escritura en tres ViewSets

Solo `RegistroCosechaViewSet` implementa `get_permissions()`. `Supervisor`, `Trabajador` y
`Cuartel` no lo tienen, por lo que dependen del `IsAuthenticated` por defecto: cualquier
usuario autenticado puede crear, editar o borrar esos recursos. El enunciado (11.4) exige
que `Supervisor`/`Cuartel` sean crear/editar/borrar solo admin, y `Trabajador` crear/editar
solo admin.
Dirección: las restricciones de escritura por acción van en `get_permissions()` de cada
ViewSet, no en `get_queryset()`.

### 3. Auditoría de trabajadores ausente

El enunciado (11.5) pide auditar como mínimo `crear_registro`, `editar_registro`,
`eliminar_registro`, `crear_trabajador` y `desactivar_trabajador`. `TrabajadorViewSet` no
audita nada: faltan dos de las cinco acciones obligatorias.
Dirección: el registro de auditoría se engancha en los hooks de creación/actualización del
ViewSet de trabajadores, igual que en registros.

### 4. Acceso a un registro de otra cuadrilla no devuelve 403

El enunciado (11.4) exige que un supervisor que accede a un registro de otra cuadrilla reciba
un 403, validado en `get_object()`. Como `get_object()` llama a `super().get_object()` sobre
un `get_queryset` ya filtrado, el objeto de otra cuadrilla no se encuentra y la respuesta es
un 404, no el 403 pedido. El caso no está cubierto por tests ni por el `.http`.
Dirección: para distinguir "no existe" de "existe pero no te pertenece" hace falta resolver
el objeto sin el filtro de cuadrilla y validar la pertenencia aparte.

### 5. El manejo de `DecimalField` no se resolvió ni se documentó

El enunciado (11.2) lo pide de forma explícita: los `DecimalField` se serializan como string
por defecto, el frontend espera números, y hay que decidir y documentar una estrategia
consistente en toda la API. Hoy `kilos`, `horas` y `hectareas` salen como string en los
serializers, mientras que `rendimiento`, `kilos_acumulados` y los agregados de los `@action`
salen como número. La salida de `/api/registros/` y la de `/api/registros/resumen/` no son
consistentes.
Dirección: definir una sola convención (string o número) y aplicarla a todos los campos
decimales y campos calculados, dejándola documentada.

---

## Pendiente — funcionalidad incompleta

### 6. Faltan los filtros por query param (11.4)

No están implementados:

- registros: `?trabajador_rut=`, `?cuartel=`, `?calidad=`, `?desde=`, `?hasta=`
- trabajadores: `?supervisor_rut=`, `?activo=`, `?buscar=`

Dirección: el filtrado por query param se aplica sobre el queryset del ViewSet.

### 7. Filtros de `AuditLogViewSet` ausentes (11.5)

Se piden `?usuario=`, `?accion=`, `?modelo=`, `?desde=`, `?hasta=`. No hay ninguno.
Dirección: mismo mecanismo de filtrado que en el punto 6, aplicado al queryset de auditoría.

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
- Que cada edición deje un `AuditLog` con `datos_previos`/`datos_nuevos` correctos. El test
  actual `test_auditoria_registro` solo crea un `AuditLog` a mano y no ejercita el flujo real,
  por eso el bug del punto 1 pasó inadvertido.

Dirección: cada test debe afirmar sobre el contenido de la respuesta o la base de datos, no
solo sobre el código de estado.

### 9. `resumen` accesible para trabajador

`GET /api/registros/resumen/` debería ser admin/supervisor (11.4), pero `get_permissions()`
no contempla la acción `resumen` y cae en el `IsAuthenticated` por defecto, de modo que un
trabajador autenticado también puede llamarla.
Dirección: la acción `resumen` necesita la misma restricción de rol que el resto de la
escritura del ViewSet.

### 10. Falta `frontend/campo-web/.env.local.example`

El enunciado (11.10.2) lo pide como entregable. No existe en el repo, aunque la variable sí
está documentada en el README. Además, el `.gitignore` del frontend ignora `.env*`, lo que
también taparía ese archivo de ejemplo.
Dirección: crear el archivo de ejemplo y asegurar que el `.gitignore` no lo excluya.

---

## Detalles menores

### 11. Posible N+1 (regla de oro nº5 del proyecto)

- `SupervisorSerializer` ejecuta `obj.trabajadores.count()` y `obj.cuarteles.count()` por
  fila. Al listar supervisores —y al listar trabajadores, porque anida el supervisor
  completo— se dispara una consulta por registro.
- `CuartelSerializer.get_kilos_acumulados` ejecuta un `aggregate` por cada cuartel: no es loop
  en Python, pero sí una query por fila al listar.

Dirección: estos conteos y sumas pueden resolverse con `annotate` en el queryset del ViewSet
en una sola consulta. El número de queries se mide con Django Debug Toolbar o `assertNumQueries`.

### 12. Los `@action` resuelven por id en vez de por `rut`/`nombre`

El enunciado define `/api/trabajadores/<rut>/rendimiento/` y
`/api/cuarteles/<nombre>/productividad/`. La implementación resuelve por el `id` (pk) por
defecto, lo que funciona pero no coincide con la ruta pedida.
Dirección: el campo de búsqueda del ViewSet determina cómo se resuelve el detalle.

### 13. README con formato roto

- Los títulos `##Levantar`, `###1-...` no llevan espacio tras los `#`, por lo que no se
  renderizan como encabezados.
- El comando del entorno virtual está pegado en una sola línea:
  `python -m venv venvsource venv/bin/activate`, que falla al copiarse.

### 14. Ubicación de `requirements.txt`

El enunciado lo ubica en `backend/requirements.txt`; está en
`backend/proyecto_django/requirements.txt`. No calza con el árbol de entrega.

### 15. Indentación de comentarios en `views.py`

Algunos comentarios dentro de `RegistroCosechaViewSet` (los de `resumen` y `get_permissions`)
quedaron mal indentados. No afecta la ejecución.

### 16. Choices sin tilde

El modelo usa `'Exportacion'` y el enunciado escribe `Exportación`. Es consistente dentro del
código, así que no es un error; queda como decisión tomada.

---

## Resumen

| Área | Estado |
|------|--------|
| Modelos y migración | Sólido |
| Serializers | Bien, falta resolver Decimals (5) |
| Auth / JWT / me | Bien |
| Visibilidad `get_queryset` | Bien |
| Permisos de escritura | Incompletos (2) |
| Auditoría | Edición rota (1) y trabajador ausente (3) |
| 403 en `get_object` | Devuelve 404 (4) |
| Filtros query param | Faltan (6, 7) |
| Tests | No cubren lo exigido (8) |
| Frontend | Conecta; falta `.env.local.example` (10) |
| Documentación y estructura | Detalles (13, 14) |

Los puntos 1 a 5 son prioritarios: afectan correctitud y seguridad, y varios estaban
advertidos de forma explícita en el enunciado.
