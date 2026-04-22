/*1- POBLAR TABLA
	Agregar 30 temporeros = +
terrasoft_2026=> INSERT INTO temporeros {
terrasoft_2026-> nombre,
terrasoft_2026-> rut,
terrasoft_2026-> telefono,
terrasoft_2026-> contacto_emergencia,
terrasoft_2026-> fecha_ingreso,
terrasoft_2026-> supervisor,
terrasoft_2026-> fecha_nacimiento^C
terrasoft_2026=> INSERT INTO temporeros (
terrasoft_2026(> nombre,
terrasoft_2026(> rut,
terrasoft_2026(> telefono,
terrasoft_2026(> contacto_emergencia,
terrasoft_2026(> fecha_ingreso,
terrasoft_2026(> supervisor,
terrasoft_2026(> fecha_nacimiento
terrasoft_2026(> )
terrasoft_2026-> VALUES (
terrasoft_2026(> 'Carlos Muñoz',
terrasoft_2026(> '12345678-9',
terrasoft_2026(> '912345678',
terrasoft_2026(> 'Ana Muñoz',
terrasoft_2026(> '2026-04-10',
terrasoft_2026(> TRUE,
terrasoft_2026(> '1985-06-15'
terrasoft_2026(> );
INSERT 0 1

2- CAMBIOS DE ESQUEMA
	Agregar columnas talla_polera S-M-L-XL = hecho
		ALTER TABLE (según entiendo altera la tabla)
		ADD COLUMN (para agregar otra columna)
		CHECK constraint (para chequear que el campo no quede vacio)
	Rellenar talla de los ya registrados = hecho
	Agregar una columna "activo" de tipo BOOL, por defecto en TRUE = hecho
		terrasoft_2026=> ALTER TABLE temporeros
		terrasoft_2026-> ADD COLUMN activo
		terrasoft_2026-> BOOLEAN DEFAULT TRUE;
		ALTER TABLE
	Corregir nombre mal escrito = hecho
		terrasoft_2026=> SELECT * FROM temporeros;
		terrasoft_2026=> SELECT * FROM temporeros WHERE nombre = 'Maria Soto';
		terrasoft_2026=> UPDATE temporeros
		terrasoft_2026-> SET nombre = 'Mariana Soto'
		terrasoft_2026-> WHERE nombre = 'Maria Soto';
		UPDATE 1
<Es importante ya que debemos saber y visualizar que queremos actualizar o eliminar, de esta manera no se arriesga a borrar datos importantes.
	Dar de baja a temporeros = hecho
		terrasoft_2026=> SELECT * FROM temporeros
		terrasoft_2026-> WHERE id IN (7,14,21);
		terrasoft_2026=> UPDATE temporeros
		terrasoft_2026-> SET activo = FALSE
		terrasoft_2026-> WHERE id IN (7,14,21);
		UPDATE 3
		terrasoft_2026=> SELECT * FROM temporeros
		terrasoft_2026-> WHERE activo = FALSE;
		Al ejecutarla me da los 3 temporeros inactivos

*/
