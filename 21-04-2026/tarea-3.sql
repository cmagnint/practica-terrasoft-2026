/* Intenta insertar un onceavo temporero con un RUT que ya existe
🚨 ¿Qué error lanza la base de datos? Cópialo tal cual en un comentario.
INSERT INTO temporeros (nombre, rut) VALUES ('Prueba','11111111-1');
ERROR: duplicate key value violates unique constraint "temporeros_rut_key"
1¿Cuántos temporeros no dejaron teléfono ?
SELECT COUNT(*) 
FROM temporeros
WHERE telefono IS NULL;
2
2¿Qué supervisores hay contratados?
SELECT nombre
FROM temporeros
WHERE supervisor = TRUE;
4
3¿Quién fue el primero en entrar esta temporada?
SELECT nombre
FROM temporeros
ORDER BY fecha_ingreso ASC
LIMIT 1;
Jorge Torres
4-Muestra el nombre y la edad de cada temporero, calculada a partir de su fecha de nacimiento.
SELECT nombre, DATE_PART('year', AGE(fecha_nacimiento)) AS edad
FROM temporeros;
 
 Juan Perez     |   60
 Pedro Soto     |   23
 Maria Soto     |   25
 Ana Lopez      |   31
 Luis Lopez     |   20
 Carlos Diaz    |   65
 Diego Ruiz     |   27
 Sofia Reyes    |   23
 Jorge Torres   |   55
 Valentina Rios |   36

5¿Cuántos temporeros son mayores de 40 años?
SELECT COUNT(*)
FROM temporeros
WHERE DATE_PART('year', AGE(fecha_nacimiento)) > 40;
3
¿Por qué elegiste ese tipo de dato para el RUT ? ¿Qué pasa si lo guardas como número entero?
El rut al contener números, guion y digito verificador, es mas conveniente asignarle un varchar, si se guardara como entero por ejemplo, perdería el formato y no dejaría validar correctamente el digito verificador

¿Qué diferencia hay entre un campo en NULLy un campo con texto vacío('') ? ¿Cuál conviene para el teléfono?
NULL significa que no hay dato, y es un área al que se puede dejar vacio
Y ya que como menciona el ejemplo, no todos tienen celular, es mejor dejar el espacio en blanco

¿Por qué el jefe tiene razón en pedir fecha de nacimiento en vez de edad directa? ¿Qué problema tendrías si hubieras guardado solo la edad?
Tiene razón en que la edad cambia cada año, con la fecha de nacimiento se podría calcular en cualquier momento, en cambio si se guarda solo la edad, esta se ira desactualizando con cada año que pase

Si más adelante tuvieras que registrar las labores que hace cada temporero (poda, cosecha, riego, etc.), ¿agregarías una columna a esta misma tabla o harías algo distinto? Explica.
Haria otra tabla, para no saturar con columnas y asi llevar una mayor flexibilidad y orden en los datos
