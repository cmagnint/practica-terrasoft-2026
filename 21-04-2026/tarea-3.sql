DROP TABLE IF EXISTS temporeros;

CREATE TABLE temporeros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    rut VARCHAR(12) UNIQUE NOT NULL,
    telefono VARCHAR(15),
    contacto_emergencia VARCHAR(100),
    fecha_ingreso DATE NOT NULL,
    supervisor BOOLEAN DEFAULT FALSE,
    fecha_nacimiento DATE NOT NULL
);

INSERT INTO temporeros (nombre, rut, telefono, contacto_emergencia, fecha_ingreso, supervisor, fecha_nacimiento) VALUES
('Juan Perez', '11111111-1', NULL, 'Maria Perez', '2026-03-10', FALSE, '1965-05-10'),
('Pedro Soto', '22222222-2', '912345678', 'Carlos Soto', '2026-04-15', TRUE, '2002-08-20'),
('Maria Soto', '33333333-3', '923456789', 'Carlos Soto', '2026-04-10', FALSE, '2000-03-12'),
('Ana Lopez', '44444444-4', '934567890', 'Luis Lopez', '2026-03-25', TRUE, '1995-07-18'),
('Luis Lopez', '55555555-5', NULL, 'Luis Lopez', '2026-04-18', FALSE, '2004-11-22'),
('Carlos Diaz', '66666666-6', '945678901', 'Ana Diaz', '2026-03-01', TRUE, '1958-02-14'),
('Diego Ruiz', '77777777-7', '956789012', 'Pedro Ruiz', '2026-04-05', FALSE, '1998-09-30'),
('Sofia Reyes', '88888888-8', NULL, 'Laura Reyes', '2026-04-12', TRUE, '2003-06-25'),
('Jorge Torres', '99999999-9', '967890123', 'Miguel Torres', '2026-02-20', FALSE, '1970-01-01'),
('Valentina Rios', '10101010-1', '978901234', 'Claudia Rios', '2026-04-20', FALSE, '1989-12-05');

-- Intento de RUT duplicado
INSERT INTO temporeros (nombre, rut, telefono, contacto_emergencia, fecha_ingreso, supervisor, fecha_nacimiento)
VALUES ('Carlos Ortega', '11111111-1', '999999999', 'Gustabo Garcia', '2026-04-22', FALSE, '2000-01-01');

-- ERROR: duplicate key value violates unique constraint "temporeros_rut_key"

-- ¿Cuántos temporeros no dejaron teléfono?
SELECT COUNT(*)
FROM temporeros
WHERE telefono IS NULL;

-- ¿Qué supervisores hay contratados?
SELECT nombre
FROM temporeros
WHERE supervisor = TRUE;

-- ¿Quién fue el primero en entrar esta temporada?
SELECT nombre
FROM temporeros
ORDER BY fecha_ingreso ASC
LIMIT 1;

-- Muestra el nombre y la edad de cada temporero, calculada a partir de su fecha de nacimiento
SELECT nombre, DATE_PART('year', AGE(fecha_nacimiento)) AS edad
FROM temporeros;

-- ¿Cuántos temporeros son mayores de 40 años?
SELECT COUNT(*)
FROM temporeros
WHERE DATE_PART('year', AGE(fecha_nacimiento)) > 40;

-- ¿Por qué elegiste ese tipo de dato para el RUT? ¿Qué pasa si lo guardas como número entero?
-- El RUT se guarda como VARCHAR porque contiene números, guion y dígito verificador.
-- Si se guardara como entero, se perdería el formato y no podría almacenarse correctamente.

-- ¿Qué diferencia hay entre un campo en NULL y un campo con texto vacío ('')? ¿Cuál conviene para el teléfono?
-- NULL significa ausencia de dato, mientras que '' representa un texto vacío.
-- Para el teléfono conviene NULL cuando la persona no entrega la información.
