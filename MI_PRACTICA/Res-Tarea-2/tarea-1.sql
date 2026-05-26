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

INSERT INTO temporeros (
  nombre,
  rut,
  telefono,
  contacto_emergencia,
  fecha_ingreso,
  supervisor,
  fecha_nacimiento
)
VALUES
('Juan Perez','11111111-1','912345678','Carlos Perez','2026-03-01',TRUE,'1965-05-10'),
('Pedro Soto','22222222-2',NULL,'Carlos Soto','2026-04-10',FALSE,'2003-02-15'),
('Maria Soto','33333333-3','987654321','Carlos Soto','2026-04-12',TRUE,'2000-08-20'),
('Ana Lopez','44444444-4','955555555','Luis Lopez','2026-02-20',FALSE,'1995-01-01'),
('Luis Lopez','55555555-5',NULL,'Luis Lopez','2026-04-18',FALSE,'2005-06-10'),
('Carlos Diaz','66666666-6','933333333','Pedro Diaz','2026-03-15',TRUE,'1960-09-09'),
('Diego Ruiz','77777777-7','944444444','Pedro Ruiz','2026-03-22',FALSE,'1998-11-11'),
('Sofia Reyes','88888888-8','922222222','Maria Reyes','2026-04-19',FALSE,'2002-12-12'),
('Jorge Torres','99999999-9','911111111','Ana Torres','2026-01-15',TRUE,'1970-07-07'),
('Valentina Rios','10101010-1','900000000','Ana Rios','2026-04-21',FALSE,'1990-03-03'),
('Daniela Rojas','15151515-5','965432123','Marta Rojas','2026-04-15',TRUE,'1990-06-10'),
('Ricardo Silva','16161616-6',NULL,'Juan Silva','2026-04-02',FALSE,'1972-09-18'),
('Camila Torres','17171717-7','912000111','Ana Torres','2026-04-12',TRUE,'1998-01-25'),
('Jose Herrera','18181818-8',NULL,'Luis Herrera','2026-04-05',TRUE,'1999-04-14'),
('Patricia Fuentes','19191919-9','934567890','Ana Fuentes','2026-04-01',FALSE,'1985-11-30'),
('Miguel Castro','20202020-0','945678901','Carlos Castro','2026-03-28',FALSE,'1979-07-22'),
('Andrea Paredes','21212121-1',NULL,'Julia Paredes','2026-04-10',TRUE,'2002-03-19'),
('Sebastian Araya','22222222-0','956789012','Pedro Araya','2026-04-12',FALSE,'1995-08-11'),
('Claudia Bravo','23232323-2','967890123','Mario Bravo','2026-03-25',FALSE,'1988-12-05'),
('Fernando Salazar','24242424-4',NULL,'Laura Salazar','2026-04-03',TRUE,'1970-02-17'),
('Natalia Godoy','25252525-5','978901234','Daniel Godoy','2026-04-18',FALSE,'1993-09-09'),
('Victor Carrasco','26262626-6','989012345','Rosa Carrasco','2026-03-29',FALSE,'1980-04-28'),
('Paula Espinoza','27272727-7',NULL,'Claudia Espinoza','2026-04-06',TRUE,'2001-05-16'),
('Rodrigo Figueroa','28282828-8','991234567','Luis Figueroa','2026-04-20',FALSE,'1992-10-02'),
('Monica Caceres','29292929-9','992345678','Elena Caceres','2026-04-07',FALSE,'1987-03-13'),
('Diego Maldonado','30303030-3','993456789','Pedro Maldonado','2026-03-27',FALSE,'1996-06-21'),
('Carolina Vera','31313131-3','994567890','Ana Vera','2026-04-09',FALSE,'1989-01-30'),
('Francisco Navarro','32323232-3','995678901','Laura Navarro','2026-04-08',FALSE,'1986-10-12'),
('Isabel Contreras','33333334-4',NULL,'Pedro Contreras','2026-04-11',FALSE,'1994-02-27'),
('Hector Morales','34343434-4','996789012','Claudia Morales','2026-03-30',FALSE,'1978-07-19');


--2- CAMBIOS DE ESQUEMA
--	Agregar columnas talla_polera S-M-L-XL = hecho
		ALTER TABLE temporeros
		ADD COLUMN talla_polera VARCHAR(2)
		CHECK (talla_polera IN ('S','M','L','XL'));

		--ALTER TABLE (según entiendo altera la tabla)
		--ADD COLUMN (para agregar otra columna)
		--CHECK constraint (para chequear que el campo no quede vacio)
--	Rellenar talla de los ya registrados = hecho
		UPDATE temporeros SET talla_polera = 'S' WHERE id BETWEEN 1 AND 6;
		UPDATE temporeros SET talla_polera = 'M' WHERE id BETWEEN 7 AND 10;
		UPDATE temporeros SET talla_polera = 'L' WHERE id BETWEEN 11 AND 16;
		UPDATE temporeros SET talla_polera = 'XL' WHERE id BETWEEN 17 AND 30;

--	Agregar una columna "activo" de tipo BOOL, por defecto en TRUE = hecho
		ALTER TABLE temporeros
		ADD COLUMN activo BOOLEAN DEFAULT TRUE;
--	Corregir nombre mal escrito = hecho
		SELECT * FROM temporeros
		WHERE nombre = 'Maria Soto';
		UPDATE temporeros
		SET nombre = 'Mariana Soto'
		WHERE nombre = 'Maria Soto';

		SELECT * FROM temporeros
		WHERE nombre = 'Mariana Soto';

--<Es importante el uso del SELECT ya que debemos saber y visualizar que queremos actualizar o eliminar, de esta manera no se arriesga a borrar datos importantes.
--	Dar de baja a temporeros = hecho
		SELECT * FROM temporeros
		WHERE id IN (7,14,21);

		UPDATE temporeros
		SET activo = FALSE
		WHERE id IN (7,14,21);

		SELECT * FROM temporeros
		WHERE activo = FALSE;


