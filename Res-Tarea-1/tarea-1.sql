/* 
\l = sirve para listar las base de datos que existen
\du = sirve para listar todos los roles existentes
\conninfo = muestra informacion detallada sobre la conexion a la bdd
\? = ayuda con los comandos de la consola
\q = sirve para salir de la consulta

Systemctl
systemctl status postgresql

1- ¿Que diferencia hay entre el servicio de PostgreSQL y el programa psql?
PostgreSQL es el sistema para la gestion de base de datos
psql es una interfaz de terminal para PostgreSQL
2- ¿Porque al instalar PostgreSQL se crea automáticamente un usuario llamado postgresen tu sistema operativo?
Se crea por temas de seguridad y administracion propia de los sistemas tipo unix
3- ¿Cuando escribes \l, ¿aparecen bases de datos que tú no creaste? ¿Para qué sirven?
Sirven como el motor de la base de datos para funcionar y organizarse sin que el usuario tenga que configruar todo desde cero
La primera "postgres" sirve como punto de entrada ya que postgresql necesita estar conectado para ejecutar comandos, seria como una sala de espera mientras creas, borras, cambias usuarios y configuraciones
La segunda "template1" es la plantilla que se copia cada vez que se crea una base de datos nueva
La tercera "template0" Es un respaldo protegido que no cambia
*/
