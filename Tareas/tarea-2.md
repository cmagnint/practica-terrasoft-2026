# 📘 Día 2 — Consultas y primer contacto con Python

> **Objetivo del día:** Dominar las consultas SQL que vas a ver todos los días cuando trabajes con Django ORM, y escribir tu primer programa Python que se conecta a una base de datos.

---

## 🛠️ Antes de empezar: estructura de tu trabajo

Hoy vas a completar **3 tareas**. Misma lógica que ayer: cada una en su propio archivo.

### 📁 Estructura que debes crear

Dentro del repositorio, crea una carpeta llamada `22-04-2026` con tres archivos:

- `tarea-1.sql`
- `tarea-2.sql`
- `tarea-3.py`

### 📋 Qué va en cada archivo

| Archivo | Contenido | ¿Se ejecuta? |
|---------|-----------|--------------|
| `tarea-1.sql` | Poblar la tabla + cambios de esquema + integridad | ✅ Sí, como `admin` |
| `tarea-2.sql` | Consultas que responden preguntas del jefe | ✅ Sí, como `admin` |
| `tarea-3.py` | Script Python que se conecta a PostgreSQL | ✅ Sí, con `python` |

> ⚠️ Todas las explicaciones y decisiones que tomes van como **comentarios dentro del archivo correspondiente**:
> - En `.sql` se comenta con `--`
> - En `.py` se comenta con `#`

---

## 🌱 Tarea 1: Más datos, cambios de esquema y gente que se va

📄 **Archivo:** `22-04-2026/tarea-1.sql`

El jefe de campo pasó por la oficina y te dice:

> 📝 *"Oye, con 10 temporeros no me sirve mucho el listado, necesito a toda la gente que tenemos trabajando, son como 30 en total. Ponle una columna para la talla de polera, porque la próxima semana llega el pedido de los uniformes y necesito saber cuántos S, M, L y XL pedir. Ah, y me di cuenta de algo: hay un temporero que me dijo su nombre mal el primer día y lo registraste mal, hay que corregirlo. Me mandó el nombre correcto por WhatsApp ayer. Otra cosa, se fueron unos temporeros: dos terminaron contrato la semana pasada y uno se enfermó y no va a volver. No los borres del sistema, solo márcalos como que ya no están activos, capaz que los volvamos a llamar la próxima temporada."*

### ✅ Lo que debes hacer

#### 1️⃣ Pobla la tabla

- [ ] Inserta temporeros hasta tener **al menos 30 en total**
  > 💡 Variedad obligatoria: distintas edades (entre 18 y 70), fechas de ingreso en distintas semanas del último mes, al menos 8 supervisores, al menos 5 sin teléfono, una variedad de apellidos.

#### 2️⃣ Cambios de esquema en producción

> ⚠️ La tabla ya tiene datos. No puedes borrarla. Todos los cambios deben preservar los datos existentes.

- [ ] Agrega la columna `talla_polera`, que debe aceptar **solo** los valores `'S'`, `'M'`, `'L'`, `'XL'`.
  > 🔎 Investiga `ALTER TABLE ... ADD COLUMN` y `CHECK constraint`.
- [ ] Rellena la talla de todos los temporeros que ya estaban registrados.
- [ ] Agrega una columna `activo` de tipo booleano, con valor por defecto `TRUE`.
  > 💡 Cuando un temporero se vaya, no lo borras: lo marcas como inactivo. Esto se llama **soft delete** y es una práctica estándar en la industria — permite conservar el historial y volver a contratar a la persona más adelante sin perder sus datos.

#### 3️⃣ Corrige el nombre mal escrito

- [ ] Elige un temporero de tu lista y corrígele el nombre usando `UPDATE`.
- [ ] **Antes de ejecutar el UPDATE**, escribe la misma consulta pero como `SELECT` para verificar exactamente a qué fila vas a afectar.
  > 🔎 Esto es una práctica profesional: *nunca* hagas un `UPDATE` o `DELETE` sin antes haber corrido el `SELECT` equivalente. ¿Por qué crees que es importante? Explícalo en un comentario.

#### 4️⃣ Da de baja a los temporeros que se fueron

Como pidió el jefe, hay temporeros que ya no están trabajando pero no quieres perder su registro.

- [ ] Marca como **inactivos** (`activo = FALSE`) a **al menos 3 temporeros** de tu lista.
  > 💡 Elige 3 cualquiera, no importa cuáles. Lo importante es que cuando hagas las consultas de la Tarea 2, haya diferencia entre "todos los temporeros" y "temporeros activos".
- [ ] Aplica la misma regla profesional: antes de correr el `UPDATE`, corre un `SELECT` con la misma condición `WHERE` para verificar a quiénes vas a afectar.
- [ ] Después de marcarlos como inactivos, escribe una consulta que te muestre **solo los inactivos**, para dejar constancia de quiénes son.

---

## 🔍 Tarea 2: Consultas del día a día

📄 **Archivo:** `22-04-2026/tarea-2.sql`

> ⚠️ Este es el tipo de consultas que Django ORM va a generar por ti más adelante. Hoy las escribes a mano para entender qué hace el ORM por debajo.

El jefe te dispara pedidos a lo largo del día, cada vez más específicos y más difíciles:

> 📝 *"Necesito varios datos, en este orden:*
>
> 1. *Lista de todos los temporeros activos ordenados por fecha de ingreso, del más nuevo al más antiguo.*
> 2. *Solo los nombres y RUT de los supervisores activos, ordenados alfabéticamente.*
> 3. *Cuántos temporeros activos tengo en total.*
> 4. *Cuántos son supervisores y cuántos no (en la misma consulta, no en dos).*
> 5. *El promedio de edad de los supervisores comparado con el promedio de los no-supervisores (en una sola consulta).*
> 6. *Cuántos temporeros hay por cada talla de polera, ordenados de la talla más pedida a la menos pedida.*
> 7. *Los nombres de los temporeros cuyo nombre empieza con 'J' o 'M', sin importar mayúsculas o minúsculas.*
> 8. *Los 5 temporeros más jóvenes que sean supervisores.*
> 9. *Cuántos temporeros ingresaron cada semana del último mes. Agrúpalos por semana.*
> 10. *El temporero más veterano (el que lleva más tiempo trabajando) de cada talla de polera."*

### ✅ Lo que debes hacer

Escribe una consulta `SELECT` para cada petición del jefe. Cada consulta debe ir precedida por un **comentario** que diga qué pregunta responde y por qué elegiste esa solución.

> 💡 Las consultas están ordenadas de la más fácil a la más difícil. Si te quedas pegado en alguna, avísame y te doy una pista. No busques "solución completa del ejercicio" en internet — busca cada concepto por separado y arma tu consulta.

---

## 🐍 Tarea 3: Primer contacto con Python + PostgreSQL

📄 **Archivo:** `22-04-2026/tarea-3.py`

Hasta ahora hablaste con PostgreSQL usando `psql` directamente. En la vida real, las bases de datos se consultan desde **programas** (un backend, un script, una app). Hoy vas a escribir tu primer script en Python que se conecta a tu base `terrasoft_2026` y saca información.

> ⚠️ Esto es el paso previo a Django. Lo que hagas hoy a mano, mañana lo va a hacer el ORM por ti.

### ✅ Lo que debes hacer

#### 1️⃣ Prepara el entorno

- [ ] Verifica que tienes **Python 3** instalado.
  > 🔎 Investiga cómo ver tu versión de Python desde la terminal.
- [ ] Dentro de la carpeta `22-04-2026/`, crea un **entorno virtual** (virtualenv).
  > 🔎 Investiga qué es un `venv` y por qué es mala práctica instalar paquetes directamente en el sistema. El comando parte con `python3 -m venv`.
- [ ] Activa el entorno virtual.
  > 🔎 El comando de activación depende del sistema operativo. En Linux termina en `/bin/activate`.
- [ ] Instala la librería **`psycopg2-binary`** (es el driver de PostgreSQL para Python).
  > 🔎 Se instala con `pip`.
- [ ] Genera un archivo `requirements.txt` que deje constancia de las dependencias instaladas.
  > 🔎 Investiga `pip freeze`. Este archivo sí debe ir al repositorio (a diferencia del venv).
- [ ] Agrega un archivo `.gitignore` a la raíz de tu repositorio que excluya la carpeta del `venv`.

#### 2️⃣ Escribe el script principal

Crea `tarea-3.py` que:

- [ ] Se conecte a la base `terrasoft_2026` usando el usuario `admin`
- [ ] Tenga un **menú interactivo** con las siguientes opciones:
  1. **Listar todos los temporeros activos** (mostrar nombre, RUT y edad calculada)
  2. **Buscar un temporero por RUT** (el programa pide el RUT y muestra los datos)
  3. **Agregar un temporero nuevo** (el programa pide los datos uno por uno y los inserta)
  4. **Marcar un temporero como inactivo** (soft delete — actualiza `activo = FALSE`)
  5. **Salir**
- [ ] El menú debe **volver a aparecer** después de cada operación hasta que el usuario elija "Salir".

#### 3️⃣ Manejo de errores

- [ ] ¿Qué pasa si el usuario escribe un RUT que no existe? Tu programa no debe crashear, debe mostrar un mensaje claro.
- [ ] ¿Qué pasa si intentas insertar un RUT que ya existe? Captura la excepción de `psycopg2` y muestra un mensaje amistoso en lugar del traceback.
- [ ] ¿Qué pasa si el usuario escribe una opción del menú que no existe? Maneja ese caso también.
  > 🔎 Investiga el bloque `try / except` de Python y las excepciones que lanza `psycopg2`.

---

## 📤 Entrega

Tu carpeta `22-04-2026/` debe contener:

```
22-04-2026/
├── tarea-1.sql
├── tarea-2.sql
├── tarea-3.py
└── requirements.txt
```

Y en la raíz del repositorio debe existir un archivo `.gitignore` que excluya la carpeta del venv.

> ⚠️ **NO subas la carpeta del venv al repositorio.** Si `git status` te muestra cientos de archivos cuando agregas el venv, cancela y revisa tu `.gitignore`.

Súbelo al repositorio usando el flujo de git que ya conoces.