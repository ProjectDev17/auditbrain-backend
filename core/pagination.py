from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginación estándar para el proyecto.
    - Tamaño por defecto: 25 registros
    - Tamaño máximo: 100 registros
    - Parámetro configurable: page_size
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 10000
