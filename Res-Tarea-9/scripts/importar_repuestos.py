from pathlib import Path

import pandas as pd
import requests

from api_client import API_BASE, obtener_token


#directorios principales del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'


#busca automaticamente los excel entregados en la tarea
EXCEL_FILES = sorted(
    DATA_DIR.glob('repuestos_proveedor_lote_*.xlsx')
)


#columnas obligatorias que debe tener cada archivo excel
COLUMNAS_REQUERIDAS = [
    'orden_id',
    'proveedor',
    'detalle',
    'costo_unitario',
    'cantidad',
]


def validar_columnas(df, archivo_nombre):
    """Valida que el excel tenga las columnas requeridas"""

    columnas_actuales = list(
        df.columns
    )

    for columna in COLUMNAS_REQUERIDAS:

        #si falta una columna, el archivo no se procesa
        if columna not in columnas_actuales:

            raise Exception(
                f'El archivo {archivo_nombre} '
                f'no tiene la columna {columna}'
            )


def validar_fila(fila):
    """Valida datos antes de llamar a la API"""

    errores = []

    #valida que orden_id pueda convertirse a entero
    try:
        int(fila['orden_id'])

    except Exception:

        errores.append(
            'orden_id debe ser entero'
        )

    #proveedor no puede venir vacio
    proveedor = str(
        fila['proveedor']
    ).strip()

    if proveedor == '' or proveedor.lower() == 'nan':

        errores.append(
            'proveedor no puede estar vacio'
        )

    #detalle no puede venir vacio
    detalle = str(
        fila['detalle']
    ).strip()

    if detalle == '' or detalle.lower() == 'nan':

        errores.append(
            'detalle no puede estar vacio'
        )

    #costo unitario debe ser numerico y mayor a cero
    try:
        costo_unitario = float(
            fila['costo_unitario']
        )

        if costo_unitario <= 0:

            errores.append(
                'costo_unitario debe ser mayor a 0'
            )

    except Exception:

        errores.append(
            'costo_unitario debe ser numerico'
        )

    #cantidad debe ser entera y mayor a cero
    try:
        cantidad = int(
            fila['cantidad']
        )

        if cantidad <= 0:

            errores.append(
                'cantidad debe ser mayor a 0'
            )

    except Exception:

        errores.append(
            'cantidad debe ser entero'
        )

    return errores


def agregar_error(
    errores,
    archivo_origen,
    fila_excel,
    fila,
    motivo,
    fuente
):
    """Agrega una fila al log de errores"""

    #guarda informacion suficiente para revisar el error despues
    errores.append({
        'archivo_origen': archivo_origen,
        'fila_excel': fila_excel,
        'orden_id': fila.get('orden_id'),
        'proveedor': fila.get('proveedor'),
        'detalle': fila.get('detalle'),
        'costo_unitario': fila.get('costo_unitario'),
        'cantidad': fila.get('cantidad'),
        'motivo': motivo,
        'fuente': fuente,
    })


def importar_archivo(archivo_path, headers):
    """Importa un archivo excel completo"""

    #lee la hoja Repuestos indicada en la pauta
    df = pd.read_excel(
        archivo_path,
        sheet_name='Repuestos'
    )

    #valida que el archivo tenga las columnas esperadas
    validar_columnas(
        df,
        archivo_path.name
    )

    total_filas = len(df)
    importadas_ok = 0
    errores = []

    print()
    print(f'Procesando archivo: {archivo_path.name}')
    print(f'Filas leidas:        {total_filas}')

    for idx, fila in df.iterrows():

        #fila real del excel, porque la fila 1 tiene encabezados
        fila_excel = idx + 2

        #primero se validan errores locales
        errores_locales = validar_fila(
            fila
        )

        #si hay errores locales no se llama a la api
        if errores_locales:

            agregar_error(
                errores=errores,
                archivo_origen=archivo_path.name,
                fila_excel=fila_excel,
                fila=fila,
                motivo='; '.join(errores_locales),
                fuente='validacion_local'
            )

            continue

        #datos que se enviaran al endpoint /api/repuestos/
        payload = {
            'orden': int(fila['orden_id']),
            'proveedor': str(fila['proveedor']).strip(),
            'detalle': str(fila['detalle']).strip(),
            'costo_unitario': float(fila['costo_unitario']),
            'cantidad': int(fila['cantidad']),
            'archivo_origen': archivo_path.name,
            'fila_excel': fila_excel,
        }

        #envia la fila valida a la api
        response = requests.post(
            f'{API_BASE}/repuestos/',
            headers=headers,
            json=payload
        )

        #201 significa creado correctamente
        if response.status_code == 201:

            importadas_ok += 1

        else:

            #errores de api incluyen orden no completada, orden inexistente o duplicados
            agregar_error(
                errores=errores,
                archivo_origen=archivo_path.name,
                fila_excel=fila_excel,
                fila=fila,
                motivo=response.text,
                fuente='api'
            )

    print(f'Importadas OK:       {importadas_ok}')
    print(f'Errores:             {len(errores)}')

    return {
        'archivo': archivo_path.name,
        'filas_leidas': total_filas,
        'importadas_ok': importadas_ok,
        'errores': errores,
    }


def guardar_log_errores(errores):
    """Guarda errores en excel"""

    #crea carpeta output si no existe
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    output_path = OUTPUT_DIR / 'errores_importacion.xlsx'

    df_errores = pd.DataFrame(
        errores
    )

    #si no hay errores igual se genera excel con columnas
    if df_errores.empty:

        df_errores = pd.DataFrame(
            columns=[
                'archivo_origen',
                'fila_excel',
                'orden_id',
                'proveedor',
                'detalle',
                'costo_unitario',
                'cantidad',
                'motivo',
                'fuente',
            ]
        )

    #guarda el log final en formato excel
    df_errores.to_excel(
        output_path,
        index=False
    )

    return output_path


def main():
    """Ejecuta importacion masiva"""

    print('========================================')
    print('IMPORTACION DE REPUESTOS POR LOTES')
    print('========================================')

    #si no encuentra excel, se detiene el proceso
    if not EXCEL_FILES:

        raise Exception(
            f'No se encontraron archivos Excel en {DATA_DIR}'
        )

    #obtiene token jwt para consumir la api
    token = obtener_token()

    #headers enviados en cada request a la api
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    total_archivos = 0
    total_filas = 0
    total_importadas = 0
    todos_errores = []

    #procesa cada excel encontrado en la carpeta data
    for archivo_path in EXCEL_FILES:

        resultado = importar_archivo(
            archivo_path,
            headers
        )

        total_archivos += 1
        total_filas += resultado['filas_leidas']
        total_importadas += resultado['importadas_ok']

        todos_errores.extend(
            resultado['errores']
        )

    #genera archivo excel con todos los errores encontrados
    output_path = guardar_log_errores(
        todos_errores
    )

    print()
    print('========================================')
    print('RESULTADO GENERAL')
    print('========================================')
    print(f'Total archivos:       {total_archivos}')
    print(f'Total filas leidas:   {total_filas}')
    print(f'Importadas OK:        {total_importadas}')
    print(f'Errores:              {len(todos_errores)}')
    print()
    print('Log de errores guardado en:')
    print(output_path)
    print('========================================')


if __name__ == '__main__':
    main()
