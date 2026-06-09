from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Paginacion estandar para la API"""

    #cantidad por defecto
    page_size = 20

    #permite cambiar cantidad por query param
    page_size_query_param = 'page_size'

    #limite maximo permitido
    max_page_size = 100
