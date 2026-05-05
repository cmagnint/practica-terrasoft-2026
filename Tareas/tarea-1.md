# 📘 Día 1 — Tareas

## 🛠️ Antes de empezar: estructura de tu trabajo

Hoy vas a completar **3 tareas** y cada una tiene su propio archivo `.sql`. Esto te obliga a mantener ordenado tu trabajo y facilita revisar cada tema por separado.

### 📁 Estructura que debes crear

Dentro del repositorio, crea una carpeta llamada `21-04-2026` y dentro de ella tres archivos vacíos:

- `tarea-1.sql`
- `tarea-2.sql`
- `tarea-3.sql`

### 📋 Qué va en cada archivo

| Archivo | Contenido | ¿Se ejecuta? |
|---------|-----------|--------------|
| `tarea-1.sql` | Solo comentarios con tus respuestas sobre psql y sus comandos | ❌ No, es solo documentación |
| `tarea-2.sql` | Creación del usuario `admin` y la base `terrasoft_2026` + respuestas | ✅ Sí, como usuario `postgres` |
| `tarea-3.sql` | Diseño, creación, inserción y consultas de la tabla `temporeros` | ✅ Sí, como usuario `admin` |

### 🧩 Cómo mezclar SQL con respuestas

> ⚠️ **IMPORTANTE:** Todas las respuestas a las preguntas de este día deben ir como **comentarios dentro de los archivos `.sql`**. 

Cada archivo mezcla **comandos SQL reales** (que PostgreSQL ejecuta) con **comentarios** (que PostgreSQL ignora pero tú usas para responder las preguntas).

- Comentario de una línea: empieza con `--`
- Comentario de varias líneas: se envuelve entre `/* ... */`

### 🧪 Cómo probar los archivos que se ejecutan

La Tarea 1 no se ejecuta (es solo documentación), pero las tareas 2 y 3 sí.

> 🔎 Investiga cómo ejecutar un archivo `.sql` desde la terminal usando `psql`. Hay una flag que sirve para pasarle un archivo como entrada. También vas a tener que decidir con qué **usuario** y sobre qué **base de datos** corres cada archivo.

---

## 🔧 Tarea 1: Instalación psql

📄 **Archivo:** `21-04-2026/tarea-1.sql` *(solo comentarios, no se ejecuta)*

### ✅ Checklist

- [ ] Instala PostgreSQL en tu sistema
- [ ] Verifica que el servicio esté corriendo
  > 🔎 En Linux se usa `systemctl`. Investiga qué subcomando sirve para consultar el estado.
- [ ] Conéctate a `psql` con el usuario por defecto que crea la instalación
- [ ] Una vez dentro del prompt `postgres=#`, investiga qué hacen estos comandos y **anota tu explicación como comentario** en `tarea-1.sql`:

  - `\l`
  - `\du`
  - `\conninfo`
  - `\?`
  - `\q`

### 🧠 Para responder

> 💡 Todas las respuestas van como comentarios (`--`) dentro de `tarea-1.sql`.

1. ¿Qué diferencia hay entre el **servicio** de PostgreSQL y el programa **`psql`**?
2. ¿Por qué al instalar PostgreSQL se crea automáticamente un usuario llamado **`postgres`** en tu sistema operativo?
3. Cuando escribes `\l`, ¿aparecen bases de datos que tú no creaste? ¿Para qué sirven?

---

## 👤 Tarea 2: Tu propia base de datos y tu propio usuario

📄 **Archivo:** `21-04-2026/tarea-2.sql` *(se ejecuta como `postgres`)*

> ⚠️ Trabajar siempre con el superusuario `postgres` es **mala práctica**, lo mismo que andar usando `root` en Linux para todo. Vamos a crear un usuario específico para este proyecto y una base de datos que le pertenezca.

### ✅ Checklist

- [ ] Al inicio del archivo, agrega sentencias para **borrar** el usuario y la base si ya existen. Esto permite que el script se pueda ejecutar varias veces sin que falle.
  > 🔎 Las sentencias son `DROP DATABASE` y `DROP USER`. Investiga cómo agregarles una cláusula que no falle si el objeto no existe.
- [ ] Crea un usuario llamado **`admin`** con una contraseña simple
  > 🔐 Puede ser `admin123` por ahora.
- [ ] Crea una base de datos llamada **`terrasoft_2026`** y hazla propiedad del usuario `admin`
- [ ] Ejecuta el archivo desde la terminal como superusuario
  > 🔎 Recuerda: para actuar como `postgres` en Linux se usa `sudo -u`. Y `psql` tiene una flag para pasarle un archivo como input.
- [ ] Después de ejecutar, conéctate directamente con el usuario `admin` a la base `terrasoft_2026`
  > 🔎 `psql` acepta flags para especificar usuario (`-U`) y base de datos (`-d`).
- [ ] Verifica con `\conninfo` que estás conectado correctamente
  > Debe mostrar: usuario `admin` + base `terrasoft_2026` ✅
- [ ] Usa `\dt` dentro de la base. ¿Qué mensaje te devuelve y por qué?

### 🧠 Para responder

> 💡 Todas las respuestas van como comentarios (`--`) dentro de `tarea-2.sql`.

1. ¿Qué diferencia hay entre un **rol**, un **usuario** y el **dueño** de una base de datos en PostgreSQL?
2. Si creaste la base como `postgres` pero se la asignaste a `admin`, ¿quién puede borrarla? **Pruébalo.**
3. ¿Qué pasa si intentas conectarte a una base de datos que no existe? **Fuerza el error y copia el mensaje tal cual.**

---

## 🌾 Tarea 3: Primera tabla — Registro de temporeros

📄 **Archivo:** `21-04-2026/tarea-3.sql` *(se ejecuta como `admin`)*

La empresa contrató temporeros para la **cosecha de arándanos** de esta temporada. El jefe de campo te pasa esta nota a mano pidiendo que armes el registro:

> 📝 *"Oye, necesito llevar el control de la gente que está trabajando esta temporada. Anota el nombre completo y el RUT de cada uno, eso es fijo. El teléfono me gustaría tenerlo aunque hay varios que no tienen o no quieren darlo. Algunos son de la misma familia y me dan el mismo contacto de emergencia, así que ese campo puede repetirse. El RUT obviamente no, no puedo tener dos personas con el mismo RUT inscritas. También quiero saber la fecha en que entraron a trabajar y si son supervisores (supervisores ganan distinto)."*

Más tarde, cuando estabas diseñando la tabla, el jefe vuelve y agrega:

> 📝 *"Ah, se me olvidaba, también necesito saber la edad de cada uno por temas de los seguros. Pero no me hagas anotar la edad directa porque eso cambia cada año y se me va a desactualizar, mejor guarda la fecha de nacimiento y la edad la sacamos cuando la necesitemos."*

### ✅ Lo que debes hacer

#### 1️⃣ Diseña la tabla `temporeros`

Toma decisiones sobre:

- 🔢 **Qué tipo de dato usar** para cada campo
  > ⚠️ Piensa bien el RUT, tiene guión y dígito verificador
- ❗ **Qué campos son obligatorios** y cuáles pueden quedar vacíos
- 🔑 **Qué campo no puede repetirse nunca**
- 🎂 **Fecha de nacimiento** como campo aparte (no guardes la edad)

#### 2️⃣ Crea la tabla con `CREATE TABLE` dentro de la base `terrasoft_2026`

> 💡 Al inicio del archivo, agrega una sentencia para borrar la tabla si ya existe, así puedes re-ejecutar el script sin errores. Investiga cuál es.

#### 3️⃣ Inserta **10 temporeros** que incluyan obligatoriamente estos casos:

- [ ] Uno **sin teléfono**
- [ ] Dos **hermanos** con el mismo contacto de emergencia
- [ ] Al menos **3 supervisores**
- [ ] Uno que haya entrado **hace más de un mes** y otro que haya entrado **esta semana**
- [ ] Al menos uno **mayor de 50 años** y uno **menor de 25** (para que las consultas por edad tengan sentido)

#### 4️⃣ Intenta insertar un **onceavo temporero con un RUT que ya exista**

> 🚨 ¿Qué error lanza la base de datos? **Cópialo tal cual en un comentario.**

#### 5️⃣ Escribe consultas `SELECT` que respondan:

| # | Pregunta |
|---|----------|
| 1 | ¿Cuántos temporeros **no dejaron teléfono**? |
| 2 | ¿Qué **supervisores** hay contratados? |
| 3 | ¿Quién fue el **primero en entrar** esta temporada? |
| 4 | Muestra el **nombre y la edad** de cada temporero, calculada a partir de su fecha de nacimiento |
| 5 | ¿Cuántos temporeros son **mayores de 40 años**? |

> 💡 **Pista para las consultas 4 y 5:** PostgreSQL tiene funciones para trabajar con fechas. Investiga qué hacen `AGE()`, `EXTRACT()` y `CURRENT_DATE`. Hay más de una forma correcta de resolverlo.

### 🧠 Preguntas para responder

> 💡 Todas las respuestas van como comentarios (`--`) dentro de `tarea-3.sql`.

1. ¿Por qué elegiste ese tipo de dato para el **RUT**? ¿Qué pasa si lo guardas como número entero?
2. ¿Qué diferencia hay entre un campo en **`NULL`** y un campo con **texto vacío `('')`**? ¿Cuál conviene para el teléfono?
3. ¿Por qué el jefe tiene razón en pedir **fecha de nacimiento** en vez de edad directa? ¿Qué problema tendrías si hubieras guardado solo la edad?
4. Si más adelante tuvieras que registrar las **labores** que hace cada temporero (poda, cosecha, riego, etc.), ¿agregarías una columna a esta misma tabla o harías algo distinto? **Explica.**

---

## 📤 Entrega

Tu carpeta `21-04-2026/` debe contener los 3 archivos:

```
21-04-2026/
├── tarea-1.sql
├── tarea-2.sql
└── tarea-3.sql
```

Súbelos al repositorio usando el flujo de git.