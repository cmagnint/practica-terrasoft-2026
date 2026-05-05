def calcular_dv(numero: int) -> str:
    secuencia = [2, 3, 4, 5, 6, 7]
    suma = 0
    i = 0

    for digito in reversed(str(numero)):
        suma += int(digito) * secuencia[i]
        i = (i + 1) % len(secuencia)

    resto = 11 - (suma % 11)

    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)


def limpiar_rut(rut: str) -> str:
    if not rut:
        raise ValueError("RUT vacío")

    rut = rut.strip().replace(".", "").replace(" ", "").upper()

#cuando el rut est sin guion
    if "-" not in rut:
        numero = rut[:-1]
        dv = rut[-1]
    else:
        numero, dv = rut.split("-")

    if not numero.isdigit():
        raise ValueError("Parte numérica inválida")

    return f"{int(numero)}-{dv}"


def validar_rut(rut: str) -> bool:
    try:
        limpio = limpiar_rut(rut)
        numero, dv = limpio.split("-")

        dv_correcto = calcular_dv(int(numero))

        return dv == dv_correcto
    except Exception:
        return False


if __name__ == "__main__":
    print(validar_rut("15234567-4"))        # True
    print(validar_rut("15.234.567-4"))      # True
    print(validar_rut("20123456-9"))        # False

    print(limpiar_rut("15.234.567-4"))      # 15234567-4
    print(limpiar_rut("15234567K"))         # 15234567-K
    print(limpiar_rut("  15234567 - 4  "))  # 15234567-4
