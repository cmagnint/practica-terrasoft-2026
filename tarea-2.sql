1-¿Qué diferencia hay entre un rol , un usuario y el dueño de una base de d>
--El rol es la entidad general de los permisos en los usuarios
--El usuario es un rol con permiso de inicio de sesion
--El dueño de la base de datos es el rol que creó o al que se le asignó la base y tiene control total sobre ella y puede modificarla o borrarla
2-Si creaste la base como postgres pero se la asignaste a admin, ¿quién puede borrarla? Pruébalo.
-- La base de datos puede ser borrada tanto por el usuario dueño admin como por el superusuario postgres
-- Aunque la base haya sido asignada al admin, postgres tiene permisos totales sobre todas las bases del sistema, por lo tanto puede eliminarla sin restricciones
3-¿Qué pasa si intentas conectarte a una base de datos que no existe? Fuerza el error y copia el mensaje tal cual.
--chris@zChriuz:~/21-04-2026$ psql -U admin -d terrasoft_2026 -h localhost 
--Password for user admin: 
--psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL: database "terrasoft_2026" does not exist
--la misma base de datos fue borrada con el perfil postgres, como se menciona en la pregunta anterior
