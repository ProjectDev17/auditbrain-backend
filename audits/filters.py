from django_filters import rest_framework as filters
from .models import Audit

class AuditFilter(filters.FilterSet):
    """
    Filtros personalizados para el modelo Audit.
    
    Filtros disponibles:
    - status: Filtro exacto por estado
    - created_by: Filtro exacto por usuario creador
    - created_at__gte: Fecha de creación mayor o igual
    - created_at__lte: Fecha de creación menor o igual
    """
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Audit
        fields = ['id', 'status', 'created_by']
