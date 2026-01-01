from rest_framework import viewsets
from .models import Audit, AuditEvent
from . import serializers
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
    serializer_class = serializers.AuditSerializer
    filterset_class = AuditFilter
    ordering_fields = ['created_at', 'updated_at', 'status', 'title']
    ordering = ['-created_at']  # Ordenamiento por defecto
    
    def get_serializer_class(self):
        """Usar serializer de detalle para retrieve."""
        if self.action == 'retrieve':
            return serializers.AuditDetailSerializer
        return serializers.AuditSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()


class AuditEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet para eventos de calendario asociados a auditorías.
    Usa nested routes: /api/audits/{audit_id}/events/
    """
    serializer_class = serializers.AuditEventSerializer
    
    def get_queryset(self):
        audit_id = self.kwargs.get('audit_pk')
        return Audit.objects.get(id=audit_id).events.filter(deleted=False)
    
    def perform_create(self, serializer):
        audit_id = self.kwargs.get('audit_pk')
        serializer.save(audit_id=audit_id)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()


class GlobalAuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar todos los eventos de auditoría (solo lectura).
    Ruta: /api/events/
    """
    queryset = AuditEvent.objects.filter(deleted=False)
    serializer_class = serializers.AuditEventSerializer


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para evidencias/archivos asociados a auditorías.
    Usa nested routes: /api/audits/{audit_id}/evidences/
    Soporta subida de archivos multipart/form-data.
    """
    serializer_class = serializers.EvidenceSerializer
    
    def get_queryset(self):
        audit_id = self.kwargs.get('audit_pk')
        return Audit.objects.get(id=audit_id).evidences.filter(deleted=False)
    
    def perform_create(self, serializer):
        audit_id = self.kwargs.get('audit_pk')
        serializer.save(audit_id=audit_id)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()
