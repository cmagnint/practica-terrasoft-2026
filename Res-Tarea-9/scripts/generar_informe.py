from datetime import datetime
from pathlib import Path

import pandas as pd

from api_client import (
    obtener_token,
    obtener_todos,
)


#ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

#carpeta donde se guardara el informe final
OUTPUT_DIR = BASE_DIR / 'output'


def moneda(valor):
    """Formatea valores como moneda chilena"""

    return f"${valor:,.0f}".replace(
        ',',
        '.'
    )


def porcentaje(valor):
    """Formatea valores como porcentaje"""

    return f"{valor:.1f}%".replace(
        '.',
        ','
    )


def preparar_ordenes(df_ordenes):
    """Prepara dataframe de ordenes completadas"""

    #lista donde se guardaran las ordenes procesadas
    ordenes_preparadas = []

    for _, orden in df_ordenes.iterrows():

        #la api devuelve mecanico como diccionario anidado
        mecanico = orden.get(
            'mecanico',
            {}
        )

        #la api devuelve vehiculo como diccionario anidado
        vehiculo = orden.get(
            'vehiculo',
            {}
        )

        #extrae solo los datos necesarios para el informe
        ordenes_preparadas.append({
            'orden_id': orden['id'],
            'mecanico_id': mecanico.get('id'),
            'mecanico_nombre': mecanico.get('nombre'),
            'mecanico_especialidad': mecanico.get('especialidad'),
            'vehiculo_patente': vehiculo.get('patente'),
            'fecha': orden.get('fecha_entrega_real') or orden.get('fecha_ingreso'),
            'monto': float(orden.get('monto') or 0),
        })

    return pd.DataFrame(
        ordenes_preparadas
    )


def preparar_repuestos(df_repuestos):
    """Prepara dataframe de repuestos importados"""

    #si no hay repuestos, retorna estructura vacia
    if df_repuestos.empty:

        return pd.DataFrame(
            columns=[
                'orden_id',
                'costo_repuestos'
            ]
        )

    repuestos = df_repuestos.copy()

    #convierte costo_total a numero para poder sumar
    repuestos['costo_total'] = pd.to_numeric(
        repuestos['costo_total'],
        errors='coerce'
    ).fillna(0)

    #suma el costo total de repuestos por cada orden
    repuestos_por_orden = (
        repuestos
        .groupby('orden', as_index=False)['costo_total']
        .sum()
        .rename(columns={
            'orden': 'orden_id',
            'costo_total': 'costo_repuestos'
        })
    )

    return repuestos_por_orden


def construir_detalle_ordenes(df_ordenes, df_repuestos):
    """Construye detalle con margen por cada orden"""

    #prepara ordenes completadas
    ordenes = preparar_ordenes(
        df_ordenes
    )

    #prepara total de repuestos por orden
    repuestos_por_orden = preparar_repuestos(
        df_repuestos
    )

    #une ordenes con repuestos usando orden_id
    detalle = ordenes.merge(
        repuestos_por_orden,
        on='orden_id',
        how='left'
    )

    #si una orden no tiene repuestos, su costo queda en cero
    detalle['costo_repuestos'] = detalle['costo_repuestos'].fillna(0)

    #margen bruto = monto facturado - costo repuestos
    detalle['margen'] = (
        detalle['monto'] -
        detalle['costo_repuestos']
    )

    #margen porcentual por orden
    detalle['margen_pct'] = detalle.apply(
        lambda row: (
            row['margen'] / row['monto'] * 100
            if row['monto'] > 0
            else 0
        ),
        axis=1
    )

    #ordena de menor a mayor rentabilidad
    detalle = detalle.sort_values(
        by='margen_pct',
        ascending=True
    )

    return detalle


def construir_resumen_mecanicos(detalle):
    """Construye resumen de rentabilidad agrupado por mecanico"""

    #agrupa ordenes completadas por mecanico
    resumen = (
        detalle
        .groupby(
            [
                'mecanico_id',
                'mecanico_nombre',
                'mecanico_especialidad'
            ],
            as_index=False
        )
        .agg(
            ordenes_completadas=('orden_id', 'count'),
            monto_facturado=('monto', 'sum'),
            costo_repuestos=('costo_repuestos', 'sum'),
            margen_bruto=('margen', 'sum')
        )
    )

    #calcula margen porcentual por mecanico
    resumen['margen_pct'] = resumen.apply(
        lambda row: (
            row['margen_bruto'] / row['monto_facturado'] * 100
            if row['monto_facturado'] > 0
            else 0
        ),
        axis=1
    )

    #ordena por mayor rentabilidad
    resumen = resumen.sort_values(
        by='margen_pct',
        ascending=False
    )

    return resumen


def construir_ordenes_sin_repuestos(detalle):
    """Obtiene ordenes completadas que no tienen repuestos"""

    #filtra ordenes cuyo costo de repuestos es cero
    return detalle[
        detalle['costo_repuestos'] == 0
    ][
        [
            'orden_id',
            'mecanico_nombre',
            'vehiculo_patente',
            'fecha',
            'monto'
        ]
    ].copy()


def preparar_excel_resumen(resumen):
    """Prepara columnas finales del resumen por mecanico"""

    df = resumen.copy()

    #renombra columnas para mostrarlas en el excel final
    df = df.rename(columns={
        'mecanico_nombre': 'Mecánico',
        'mecanico_especialidad': 'Especialidad',
        'ordenes_completadas': 'Órdenes',
        'monto_facturado': 'Monto Facturado',
        'costo_repuestos': 'Costo Repuestos',
        'margen_bruto': 'Margen Bruto',
        'margen_pct': 'Margen %'
    })

    df = df[
        [
            'Mecanico',
            'Especialidad',
            'Ordenes',
            'Monto Facturado',
            'Costo Repuestos',
            'Margen Bruto',
            'Margen %'
        ]
    ]

    #calcula totales generales
    total_monto = df['Monto Facturado'].sum()
    total_costo = df['Costo Repuestos'].sum()
    total_margen = df['Margen Bruto'].sum()

    total_pct = (
        total_margen / total_monto * 100
        if total_monto > 0
        else 0
    )

    #fila final de totales
    fila_total = {
        'Mecanico': 'TOTAL',
        'Especialidad': '',
        'Ordenes': df['Ordenes'].sum(),
        'Monto Facturado': total_monto,
        'Costo Repuestos': total_costo,
        'Margen Bruto': total_margen,
        'Margen %': total_pct,
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame([fila_total])
        ],
        ignore_index=True
    )

    return df


def preparar_excel_detalle(detalle):
    """Prepara columnas finales del detalle de ordenes"""

    df = detalle.copy()

    #renombra columnas para la hoja detalle
    df = df.rename(columns={
        'orden_id': 'Orden ID',
        'mecanico_nombre': 'Mecanico',
        'vehiculo_patente': 'Vehiculo',
        'fecha': 'Fecha',
        'monto': 'Monto',
        'costo_repuestos': 'Costo Repuestos',
        'margen': 'Margen',
        'margen_pct': 'Margen %'
    })

    return df[
        [
            'Orden ID',
            'Mecanico',
            'Vehiculo',
            'Fecha',
            'Monto',
            'Costo Repuestos',
            'Margen',
            'Margen %'
        ]
    ]


def preparar_excel_sin_repuestos(ordenes_sin_repuestos):
    """Prepara hoja de ordenes sin repuestos"""

    #si no hay ordenes sin repuestos, la hoja igual se crea
    if ordenes_sin_repuestos.empty:

        return pd.DataFrame({
            'Mensaje': [
                'Todas las ordenes tienen repuestos registrados'
            ]
        })

    df = ordenes_sin_repuestos.copy()

    df = df.rename(columns={
        'orden_id': 'Orden ID',
        'mecanico_nombre': 'Mecanico',
        'vehiculo_patente': 'Vehiculo',
        'fecha': 'Fecha',
        'monto': 'Monto'
    })

    return df[
        [
            'Orden ID',
            'Mecanico',
            'Vehiculo',
            'Fecha',
            'Monto'
        ]
    ]


def aplicar_formato_excel(writer, df_resumen, df_detalle):
    """Aplica formato basico al excel final"""

    workbook = writer.book

    #formato para valores monetarios
    formato_moneda = workbook.add_format({
        'num_format': '$#,##0'
    })

    #formato para porcentajes
    formato_porcentaje = workbook.add_format({
        'num_format': '0.0%'
    })

    #formato para encabezados
    formato_header = workbook.add_format({
        'bold': True
    })

    hoja_resumen = writer.sheets['Resumen por Mecanico']
    hoja_detalle = writer.sheets['Detalle de Ordenes']

    #ajusta ancho de columnas en resumen
    hoja_resumen.set_column('A:A', 22)
    hoja_resumen.set_column('B:B', 18)
    hoja_resumen.set_column('C:C', 10)
    hoja_resumen.set_column('D:F', 18, formato_moneda)
    hoja_resumen.set_column('G:G', 12)

    #ajusta ancho de columnas en detalle
    hoja_detalle.set_column('A:A', 10)
    hoja_detalle.set_column('B:B', 22)
    hoja_detalle.set_column('C:C', 14)
    hoja_detalle.set_column('D:D', 14)
    hoja_detalle.set_column('E:G', 18, formato_moneda)
    hoja_detalle.set_column('H:H', 12)

    #escribe encabezados en negrita para resumen
    for col_num, value in enumerate(df_resumen.columns.values):

        hoja_resumen.write(
            0,
            col_num,
            value,
            formato_header
        )

    #escribe encabezados en negrita para detalle
    for col_num, value in enumerate(df_detalle.columns.values):

        hoja_detalle.write(
            0,
            col_num,
            value,
            formato_header
        )

    #convierte margen porcentual a formato decimal de excel
    for row in range(1, len(df_resumen) + 1):

        value = df_resumen.iloc[row - 1]['Margen %'] / 100

        hoja_resumen.write_number(
            row,
            6,
            value,
            formato_porcentaje
        )

    for row in range(1, len(df_detalle) + 1):

        value = df_detalle.iloc[row - 1]['Margen %'] / 100

        hoja_detalle.write_number(
            row,
            7,
            value,
            formato_porcentaje
        )

    #crea grafico de barras solicitado por la pauta
    chart = workbook.add_chart({
        'type': 'column'
    })

    #se excluye la fila total del grafico
    last_row = max(
        len(df_resumen) - 1,
        1
    )

    chart.add_series({
        'name': 'Monto Facturado',
        'categories': [
            'Resumen por Mecanico',
            1,
            0,
            last_row,
            0
        ],
        'values': [
            'Resumen por Mecanico',
            1,
            3,
            last_row,
            3
        ],
    })

    chart.add_series({
        'name': 'Costo Repuestos',
        'categories': [
            'Resumen por Mecanico',
            1,
            0,
            last_row,
            0
        ],
        'values': [
            'Resumen por Mecanico',
            1,
            4,
            last_row,
            4
        ],
    })

    chart.set_title({
        'name': 'Monto Facturado vs Costo Repuestos'
    })

    chart.set_x_axis({
        'name': 'Mecanico'
    })

    chart.set_y_axis({
        'name': 'Monto'
    })

    #inserta el grafico en la hoja resumen
    hoja_resumen.insert_chart(
        'I2',
        chart
    )


def generar_excel(
    resumen,
    detalle,
    ordenes_sin_repuestos
):
    """Genera archivo excel final"""

    #crea carpeta output si no existe
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    #archivo final solicitado por la pauta
    output_path = OUTPUT_DIR / 'informe_rentabilidad.xlsx'

    df_resumen = preparar_excel_resumen(
        resumen
    )

    df_detalle = preparar_excel_detalle(
        detalle
    )

    df_sin_repuestos = preparar_excel_sin_repuestos(
        ordenes_sin_repuestos
    )

    #crea excel con tres hojas
    with pd.ExcelWriter(
        output_path,
        engine='xlsxwriter'
    ) as writer:

        df_resumen.to_excel(
            writer,
            sheet_name='Resumen por Mecánico',
            index=False
        )

        df_detalle.to_excel(
            writer,
            sheet_name='Detalle de Órdenes',
            index=False
        )

        df_sin_repuestos.to_excel(
            writer,
            sheet_name='Órdenes sin repuestos',
            index=False
        )

        aplicar_formato_excel(
            writer,
            df_resumen,
            df_detalle
        )

    return output_path


def imprimir_resumen(
    resumen,
    ordenes_sin_repuestos,
    output_path
):
    """Imprime resumen en consola"""

    fecha = datetime.now().strftime(
        '%Y-%m-%d %H:%M'
    )

    print('========================================')
    print('INFORME DE RENTABILIDAD - Taller AutoServicio')
    print(f'Generado: {fecha}')
    print('========================================')
    print()
    print('RESUMEN POR MECANICO')
    print('--------------------------------------------')

    #imprime una fila por mecanico
    for _, row in resumen.iterrows():

        print(
            f"{row['mecanico_nombre']:<20} "
            f"{int(row['ordenes_completadas']):>3} "
            f"{moneda(row['monto_facturado']):>12} "
            f"{moneda(row['costo_repuestos']):>12} "
            f"{moneda(row['margen_bruto']):>12} "
            f"{porcentaje(row['margen_pct']):>8}"
        )

    #totales generales del informe
    total_ordenes = resumen['ordenes_completadas'].sum()
    total_monto = resumen['monto_facturado'].sum()
    total_costo = resumen['costo_repuestos'].sum()
    total_margen = resumen['margen_bruto'].sum()

    total_pct = (
        total_margen / total_monto * 100
        if total_monto > 0
        else 0
    )

    print('--------------------------------------------')
    print(
        f"{'TOTAL':<20} "
        f"{int(total_ordenes):>3} "
        f"{moneda(total_monto):>12} "
        f"{moneda(total_costo):>12} "
        f"{moneda(total_margen):>12} "
        f"{porcentaje(total_pct):>8}"
    )

    print()
    print('ALERTAS')
    print('--------------------------------------------')

    #cuenta ordenes completadas sin repuestos
    sin_repuestos = len(
        ordenes_sin_repuestos
    )

    #cuenta mecanicos con margen bajo
    mecanicos_bajo_margen = len(
        resumen[
            resumen['margen_pct'] < 25
        ]
    )

    if sin_repuestos > 0:

        print(
            f'{sin_repuestos} ordenes completadas sin repuestos registrados.'
        )

    else:

        print(
            'No hay ordenes completadas sin repuestos.'
        )

    if mecanicos_bajo_margen > 0:

        print(
            f'{mecanicos_bajo_margen} mecanicos con margen menor al 25%.'
        )

    else:

        print(
            'No hay mecanicos con margen menor al 25%.'
        )

    print()
    print('========================================')
    print(f'Informe guardado en: {output_path}')
    print('========================================')


def main():
    """Genera informe de rentabilidad"""

    print('Consultando API...')

    #obtiene token jwt para consumir endpoints protegidos
    token = obtener_token()

    headers = {
        'Authorization': f'Bearer {token}'
    }

    #consulta ordenes completadas
    ordenes = obtener_todos(
        'ordenes/?estado=Completada',
        headers
    )

    #consulta repuestos importados
    repuestos = obtener_todos(
        'repuestos/',
        headers
    )

    #consulta mecanicos
    mecanicos = obtener_todos(
        'mecanicos/',
        headers
    )

    #convierte respuestas json a dataframes
    df_ordenes = pd.DataFrame(
        ordenes
    )

    df_repuestos = pd.DataFrame(
        repuestos
    )

    df_mecanicos = pd.DataFrame(
        mecanicos
    )

    print(
        f'Ordenes encontradas: {len(df_ordenes)}'
    )

    print(
        f'Repuestos encontrados: {len(df_repuestos)}'
    )

    print(
        f'Mecanicos encontrados: {len(df_mecanicos)}'
    )

    #construye detalle por orden
    detalle = construir_detalle_ordenes(
        df_ordenes,
        df_repuestos
    )

    #construye resumen por mecanico
    resumen = construir_resumen_mecanicos(
        detalle
    )

    #identifica ordenes completadas sin repuestos
    ordenes_sin_repuestos = construir_ordenes_sin_repuestos(
        detalle
    )

    #genera archivo excel con tres hojas
    output_path = generar_excel(
        resumen,
        detalle,
        ordenes_sin_repuestos
    )

    #imprime resumen final en consola
    imprimir_resumen(
        resumen,
        ordenes_sin_repuestos,
        output_path
    )


if __name__ == '__main__':
    main()
