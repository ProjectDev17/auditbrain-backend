from django_filters import rest_framework as filters
from .models import Audit

class AuditFilter(filters.FilterSet):
    """
    Filtros completos para el modelo Audit.
    
    Sintaxis de uso: campo__lookup=valor
    
    Ejemplos:
    - /api/audits/?title__icontains=financiera
    - /api/audits/?status__in=pending,in_progress
    - /api/audits/?created_at__gte=2024-01-01
    - /api/audits/?description__isnull=false
    """
    
    class Meta:
        model = Audit
        fields = {
            # ID
            'id': ['exact', 'in'],
            
            # Texto - título
            'title': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith'],
            
            # Texto - descripción
            'description': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'isnull'],
            
            # Status (choices)
            'status': ['exact', 'in'],
            
            # Foreign Keys
            'audit_type': ['exact', 'in', 'isnull'],
            'auditor': ['exact', 'in', 'isnull'],
            
            # Fechas
            'start_date': ['exact', 'gt', 'gte', 'lt', 'lte', 'isnull'],
            'end_date': ['exact', 'gt', 'gte', 'lt', 'lte', 'isnull'],
            'created_at': ['exact', 'gt', 'gte', 'lt', 'lte', 'date', 'date__gte', 'date__lte'],
            'updated_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            
            # Tracking
            'created_by': ['exact', 'icontains'],
            'updated_by': ['exact', 'icontains'],
            
            # Soft delete
            'deleted': ['exact'],
        }


