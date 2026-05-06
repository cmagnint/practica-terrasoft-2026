### 1. GET exitoso — temporeros

```
[2026-05-06 19:17:41] INFO log — "GET /api/temporeros/ HTTP/1.1" 200
El usuario realizo una petición GET al endpoint /api/temporeros/.
La API respondio correctamente con codigo HTTP 200 OK,devolviendo la lista de temporeros serializada en formato JSON.

### 2. POST exitoso - creacion de labor
[2026-05-06 20:33:27] INFO log — "POST /api/labores/ HTTP/1.1" 201
El cliente envió una petición POST al endpoint /api/labores/
para crear una nueva labor.
Los datos fueron validados correctamente y almacenados en la basede datos, La API respondió con HTTP 201 Created.


### 3. Error de validación — 400
[2026-05-06 20:02:11] WARNING log — "POST /api/labores/ HTTP/1.1" 400
El cliente intento registrar una labor invalida,
La validación detecto que una labor de tipo Cosecha no incluia el campo obligatorio kilos_cosechados.
La API respondió con HTTP 400 Bad Request.

### 4. Recurso inexistente — 404
[2026-05-06 19:20:15] WARNING log — "GET /api/temporeros/99999999-9/ HTTP/1.1" 404
El cliente solicitó un temporero inexistente utilizando un RUT que no se encuentra registrado en la base de datos.
La API manejo correctamente el error devolviendo HTTP 404 Not Found.

### 5. Método no permitido — 405
[2026-05-06 20:10:40] WARNING log — "POST /api/temporeros/ HTTP/1.1" 405
El endpoint /api/temporeros/ solo acepta peticiones GET, el cliente intentó utilizar el método POST, por lo que
Django Rest Framework respondio con HTTP 405 Method Not Allowed.


### 6. Conflicto por duplicado - 409 
[2026-05-06 20:24:04] WARNING log — "POST /api/labores/ HTTP/1.1" 409
El usuario intento registrar una labor duplicada, la combinación de temporero, cuartel, tipo y fecha ya existía
en la base de datos y chocaba con la restricción UniqueConstraint
definida en el modelo Labor.
La API detectó correctamente el conflicto y respondió con
HTTP 409 Conflict.
