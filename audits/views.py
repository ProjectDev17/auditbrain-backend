from rest_framework import viewsets
from .models import Audit
from .serializers import AuditSerializer

class AuditViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar el CRUD de auditorías.
    Soporta lista, detalle, creación, actualización y borrado lógico.
    """
    queryset = Audit.objects.filter(deleted=False)
    serializer_class = AuditSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()
