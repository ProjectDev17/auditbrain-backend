from rest_framework import viewsets
from .models import Audit
from .serializers import AuditSerializer
from .filters import AuditFilter

class AuditViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar el CRUD de auditorías.
    Soporta lista, detalle, creación, actualización y borrado lógico.
    
    Filtros disponibles:
    - status, created_by, created_at__gte, created_at__lte
    
    Ordenamiento disponible:
    - created_at, updated_at, status, title
    """
    queryset = Audit.objects.filter(deleted=False)
    serializer_class = AuditSerializer
    filterset_class = AuditFilter
    ordering_fields = ['created_at', 'updated_at', 'status', 'title']
    ordering = ['-created_at']  # Ordenamiento por defecto

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()
