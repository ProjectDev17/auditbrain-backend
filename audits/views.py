from rest_framework import viewsets
from .models import Audit, AuditEvent, Evidence, AuditEvidence, AuditType
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
    serializer_class = serializers.AuditSerializer
    filterset_class = AuditFilter
    ordering_fields = '__all__'
    ordering = ['-created_at']  # Ordenamiento por defecto
    
    def get_queryset(self):
        """
        Optimized queryset with select_related for FKs and prefetch_related for M2M/Reverse FKs.
        """
        queryset = Audit.objects.filter(deleted=False).select_related(
            'audit_type', 'auditor', 'created_by', 'updated_by'
        )
        
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('events', 'evidences')
            
        return queryset

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
    ordering_fields = '__all__'
    
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
    queryset = AuditEvent.objects.filter(deleted=False).select_related('created_by', 'updated_by')
    serializer_class = serializers.AuditEventSerializer
    ordering_fields = '__all__'


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para evidencias/archivos asociados a auditorías.
    Usa nested routes: /api/audits/{audit_id}/evidences/
    Soporta subida de archivos multipart/form-data.
    """
    serializer_class = serializers.EvidenceSerializer
    ordering_fields = '__all__'
    
    def get_queryset(self):
        audit_id = self.kwargs.get('audit_pk')
        return Audit.objects.get(id=audit_id).evidences.filter(deleted=False)
    
    def perform_create(self, serializer):
        audit_id = self.kwargs.get('audit_pk')
        serializer.save(audit_id=audit_id)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()


class GlobalEvidenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar todas las evidencias de auditoría (solo lectura).
    Ruta: /api/evidences/
    """
    queryset = Evidence.objects.filter(deleted=False).select_related('created_by', 'updated_by')
    serializer_class = serializers.EvidenceSerializer
    ordering_fields = '__all__'


class AuditEvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asociaciones Audit-Evidence.
    Ruta: /api/audit-evidences/
    """
    queryset = AuditEvidence.objects.filter(deleted=False)
    serializer_class = serializers.AuditEvidenceSerializer
    ordering_fields = '__all__'

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()


class AuditTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para tipos de auditoría.
    Ruta: /api/audit-types/
    """
    queryset = AuditType.objects.filter(deleted=False)
    serializer_class = serializers.AuditTypeSerializer
    ordering_fields = '__all__'

    def perform_destroy(self, instance):
        instance.delete()
