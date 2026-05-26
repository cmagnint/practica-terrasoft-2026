# Logs Anotados — API Django REST

### 1. GET exitoso — temporeros

```log
[2026-05-06 19:17:41] INFO log — "GET /api/temporeros/ HTTP/1.1" 200 4821
```

El usuario realizó una petición GET al endpoint `/api/temporeros/`.
La API respondió correctamente con código HTTP 200 OK,
devolviendo la lista de temporeros serializada en formato JSON.

---

### 2. POST exitoso — creación de labor

```log
[2026-05-06 20:33:27] INFO log — "POST /api/labores/ HTTP/1.1" 201 266
```

El cliente envió una petición POST al endpoint `/api/labores/`
para crear una nueva labor.

Los datos fueron validados correctamente y almacenados
en la base de datos.

La API respondió con HTTP 201 Created.

---

### 3. Error de validación — 400

```log
[2026-05-06 20:02:11] WARNING log — "POST /api/labores/ HTTP/1.1" 400 103
```

El cliente intentó registrar una labor inválida.

La validación detectó que una labor de tipo `Cosecha`
no incluía el campo obligatorio `kilos_cosechados`.

La API respondió con HTTP 400 Bad Request.

---

### 4. Recurso inexistente — 404

```log
[2026-05-06 19:20:15] WARNING log — "GET /api/temporeros/99999999-9/ HTTP/1.1" 404 72
```

El cliente solicitó un temporero inexistente utilizando
un RUT que no se encuentra registrado en la base de datos.

La API manejó correctamente el error devolviendo
HTTP 404 Not Found.

---

### 5. Método no permitido — 405

```log
[2026-05-06 20:10:40] WARNING log — "POST /api/temporeros/ HTTP/1.1" 405 40
```

El endpoint `/api/temporeros/` solo acepta peticiones GET.

El cliente intentó utilizar el método POST,
por lo que Django REST Framework respondió con
HTTP 405 Method Not Allowed.

---

### 6. Conflicto por duplicado — 409

```log
[2026-05-06 20:24:04] WARNING log — "POST /api/labores/ HTTP/1.1" 409 88
```

El usuario intentó registrar una labor duplicada.

La combinación de temporero, cuartel, tipo y fecha
ya existía en la base de datos y violaba la restricción
`UniqueConstraint` definida en el modelo `Labor`.

La API detectó correctamente el conflicto y respondió
con HTTP 409 Conflict.
