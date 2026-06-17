from rest_framework.pagination import PageNumberPagination


#paginacion general de la api
class PaginacionGeneral(PageNumberPagination):

    #cantidad por defecto
    page_size = 20

    #permite cambiar el tamaño por query param
    page_size_query_param = 'page_size'

    #limite maximo permitido
    max_page_size = 100