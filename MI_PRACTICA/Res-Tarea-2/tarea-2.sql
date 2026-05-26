--1- Lista de todos los temporeros activos ordenados por fecha de ingreso, del más nuevo al más antiguo.
SELECT * FROM temporeros
WHERE activo = TRUE
ORDER BY fecha_ingreso DESC;
--Se utilizó esta solución porque WHERE activo = TRUE filtra solo los temporeros activos y ORDER BY fecha_ingreso DESC los ordena desde el ingreso más reciente al más antiguo

--2- Solo los nombres y RUT de los supervisores activos, ordenados alfabéticamente.
SELECT nombre, rut
FROM temporeros
WHERE activo = TRUE AND supervisor = TRUE
ORDER BY nombre ASC;
--Se utilizó esta solución porque SELECT nombre, rut muestra solo las columnas necesarias, WHERE filtra a los supervisores activos y ORDER BY nombre ASC los pone en orden alfabetico

--3- Cuántos activos temporales tengo en total.
SELECT COUNT(*)
FROM temporeros
WHERE activo = TRUE;
--Se utilizó esta solución porque COUNT(*) permite contar registros y WHERE activo = TRUE hace que solo se consideren los temporeros activos

--4- Cuántos son supervisores y cuántos no (en la misma consulta, no en dos)
SELECT supervisor, COUNT(*)
FROM temporeros
GROUP BY supervisor;
--Se utilizó esta solución porque GROUP BY supervisor separa los registros entre supervisores y no supervisores y COUNT(*) cuenta cuántos hay en cada grupo 

--5- El promedio de edad de los supervisores comparado con el promedio de los no supervisores (en una sola consulta).
SELECT supervisor, AVG(DATE_PART('year', AGE(fecha_nacimiento)))
FROM temporeros
GROUP BY supervisor;
--Se utilizó esta solución porque AGE(fecha_nacimiento) calcula la edad, DATE_PART('year') toma solo los años y AVG() obtiene el promedio de edad en cada grupo definido por GROUP BY supervisor

--6- Cuántos temporeros hay por cada talla de polera, ordenados de la talla más pedida a la menos pedida.
SELECT talla_polera, COUNT(*)
FROM temporeros
GROUP BY talla_polera
ORDER BY COUNT(*) DESC;
--Se utilizó esta solución porque GROUP BY talla_polera agrupa los registros por talla, COUNT(*) cuenta cuántos hay en cada una y ORDER BY COUNT(*) DESC ordena desde la talla más usada a la menos usada

--7- Los nombres de los temporeros cuyo nombre empieza con 'J' o 'M', sin importar mayúsculas o minúsculas.
SELECT nombre
FROM temporeros
WHERE LOWER(nombre) LIKE 'j%' OR LOWER(nombre) LIKE 'm%';
--Se utilizó esta solución porque LOWER(nombre) convierte el nombre a minúsculas para ignorar mayúsculas y minúsculas, y LIKE 'j%' o LIKE 'm%' permite buscar nombres que comienzan con esas letras

--8- Los 5 temporeros más jóvenes que sean supervisores.
SELECT * FROM temporeros
WHERE supervisor = TRUE
ORDER BY fecha_nacimiento DESC
LIMIT 5;
--Se utilizó esta solución porque WHERE supervisor = TRUE filtra solo supervisores, ORDER BY fecha_nacimiento DESC muestra primero a los más jóvenes y LIMIT 5 limita el resultado a cinco registros

--9- Cuántos temporeros ingresaron cada semana del último mes. Agrúpalos por semana.
SELECT DATE_TRUNC('week', fecha_ingreso) AS semana, COUNT(*)
FROM temporeros
WHERE DATE_TRUNC('month', fecha_ingreso) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY semana
ORDER BY semana;
--Se utilizó esta solución porque DATE_TRUNC('week', fecha_ingreso) agrupa los ingresos por semana, COUNT(*) cuenta cuántos hubo en cada una, y el WHERE filtra solo los registros del mes actual

--10- El temporero más veterano (el que lleva más tiempo trabajando) de cada talla de polera."
SELECT DISTINCT ON (talla_polera) * FROM temporeros
ORDER BY talla_polera, fecha_ingreso ASC;
--Se utilizó esta solución porque DISTINCT ON (talla_polera) permite obtener un solo registro por talla y ORDER BY talla_polera, fecha_ingreso ASC hace que se elija al que ingresó primero, es decir, al más veterano

