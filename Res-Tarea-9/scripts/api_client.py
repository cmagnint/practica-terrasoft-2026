import requests

API_BASE = 'http://localhost:8000/api'

CREDENCIALES = {
    'username': 'admin_taller',
    'password': 'admin123',
}


def obtener_token():

    url = f'{API_BASE}/auth/login/'

    response = requests.post(
        url,
        json=CREDENCIALES
    )

    if response.status_code != 200:

        raise Exception(
            f'Error al autenticar: '
            f'{response.status_code} - '
            f'{response.text}'
        )

    return response.json()['access']


def extraer_resultados(data):
    """Soporta distintos formatos de respuesta:
    - DRF paginado
    - wrappers personalizados
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    if 'results' in data:
        return data['results']

    for key in [
        'ordenes',
        'mecanicos',
        'repuestos'
    ]:

        if key in data:
            return data[key]

    return []


def obtener_todos(
    endpoint,
    headers,
    params=None
):

    resultados = []

    url = f'{API_BASE}/{endpoint}'

    while url:

        response = requests.get(
            url,
            headers=headers,
            params=params
        )

        if response.status_code != 200:

            raise Exception(
                f'Error GET {url}: '
                f'{response.status_code} - '
                f'{response.text}'
            )

        data = response.json()

        resultados.extend(
            extraer_resultados(data)
        )

        if isinstance(data, dict):

            url = data.get(
                'next'
            )

        else:

            url = None

        params = None

    return resultados
