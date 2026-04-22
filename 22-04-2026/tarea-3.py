import psycopg2

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="terrasoft_2026",
        user="admin",
        password="admin123"
    )

def menu():
    print("--- MENÚ ---")
    print("1. Listar temporeros activos")
    print("2. Buscar por RUT")
    print("3. Agregar temporero")
    print("4. Marcar como inactivo")
    print("5. Salir")

while True:
    menu()
    opcion = input("Seleccione una opción: ")

    if opcion == "5":
        print("Saliendo")
        break
    elif opcion == "1":
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, rut, DATE_PART('year', AGE(fecha_nacimiento)) AS edad
            FROM temporeros
            WHERE activo = TRUE;
        """)

        resultados = cursor.fetchall()

        for fila in resultados:
            print(fila)

        cursor.close()
        conn.close()
    elif opcion == "2":
        rut = input("Ingrese el RUT: ")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, rut, telefono, contacto_emergencia, fecha_ingreso, supervisor, activo
            FROM temporeros
            WHERE rut = %s;
        """, (rut,))

        resultado = cursor.fetchone()

        if resultado:
            print(resultado)
        else:
            print("No existe un temporero con ese RUT.")

        cursor.close()
        conn.close()
    elif opcion == "3":
        nombre = input("Nombre: ")
        rut = input("RUT: ")
        telefono = input("Teléfono (Enter si no tiene): ")
        contacto = input("Contacto de emergencia: ")
        fecha_ingreso = input("Fecha ingreso (YYYY-MM-DD): ")
        supervisor = input("¿Es supervisor? (s/n): ")
        fecha_nacimiento = input("Fecha nacimiento (YYYY-MM-DD): ")

        supervisor_bool = True if supervisor.lower() == "s" else False

        if telefono == "":
            telefono = None

        try:
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO temporeros (nombre, rut, telefono, contacto_emergencia, fecha_ingreso, supervisor, fecha_nacimiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (nombre, rut, telefono, contacto, fecha_ingreso, supervisor_bool, fecha_nacimiento))

            conn.commit()
            print("Temporero agregado correctamente.")

            cursor.close()
            conn.close()

        except psycopg2.Error:
            print("Error: el RUT ya existe o hay un problema con los datos.")
    elif opcion == "4":
        rut = input("Ingrese el RUT del temporero a desactivar: ")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT nombre, rut FROM temporeros WHERE rut = %s;", (rut,))
        resultado = cursor.fetchone()

        if resultado:
            cursor.execute("UPDATE temporeros SET activo = FALSE WHERE rut = %s;", (rut,))
            conn.commit()
            print("Temporero marcado como inactivo.")
        else:
            print("No existe un temporero con ese RUT.")

        cursor.close()
        conn.close()
