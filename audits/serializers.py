from rest_framework import serializers
from .models import Audit

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = [
            'id', 'title', 'description', 'status', 
            'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted', 'deleted_by'
        ]
    
    def validate_title(self, value):
        """Validar longitud mínima del título."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "El título debe tener al menos 5 caracteres."
            )
        return value.strip()
    
    def validate(self, data):
        """Validaciones a nivel de objeto."""
        # Evitar modificaciones en auditorías eliminadas
        if self.instance and self.instance.deleted:
            raise serializers.ValidationError(
                "No se puede modificar una auditoría eliminada."
            )
        
        # Validar transiciones de estado
        if self.instance:
            current_status = self.instance.status
            new_status = data.get('status', current_status)
            
            # No permitir volver de 'completed' a 'pending'
            if current_status == Audit.Status.COMPLETED and new_status == Audit.Status.PENDING:
                raise serializers.ValidationError({
                    'status': "No se puede cambiar de 'completed' a 'pending'."
                })
            
            # No permitir volver de 'completed' a 'in_progress'
            if current_status == Audit.Status.COMPLETED and new_status == Audit.Status.IN_PROGRESS:
                raise serializers.ValidationError({
                    'status': "No se puede cambiar de 'completed' a 'in_progress'."
                })
        
        return data


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de calendario de auditorías."""
    
    class Meta:
        model = Audit.events.rel.related_model  # AuditEvent
        fields = [
            'id', 'title', 'description', 'event_date',
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
    
    def validate_title(self, value):
        """Validar longitud mínima del título del evento."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El título del evento debe tener al menos 3 caracteres."
            )
        return value.strip()


class EvidenceSerializer(serializers.ModelSerializer):
    """Serializer para evidencias/archivos de auditorías."""
    
    ALLOWED_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx', 'txt', 'csv']
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    class Meta:
        model = Audit.evidences.rel.related_model  # Evidence
        fields = [
            'id', 'file', 'file_type', 'uploaded_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'file_type', 'uploaded_at', 'created_by', 'updated_by'
        ]
    
    def validate_file(self, value):
        """Validar tipo y tamaño de archivo."""
        # Validar extensión
        ext = value.name.split('.')[-1].lower()
        if ext not in self.ALLOWED_TYPES:
            raise serializers.ValidationError(
                f"Tipo de archivo no permitido. Permitidos: {', '.join(self.ALLOWED_TYPES)}"
            )
        
        # Validar tamaño
        if value.size > self.MAX_SIZE:
            raise serializers.ValidationError(
                "El archivo no puede superar 10MB."
            )
        
        return value


class AuditDetailSerializer(serializers.ModelSerializer):
    """
    Serializer extendido para detalle de auditorías.
    Incluye eventos, evidencias e historial de cambios desde MongoDB.
    """
    events = AuditEventSerializer(many=True, read_only=True)
    evidences = EvidenceSerializer(many=True, read_only=True)
    history = serializers.SerializerMethodField()
    
    class Meta:
        model = Audit
        fields = [
            'id', 'title', 'description', 'status',
            'created_at', 'updated_at',
            'created_by', 'updated_by',
            'deleted',
            'events', 'evidences', 'history'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            'deleted', 'deleted_by',
            'events', 'evidences', 'history'
        ]
    
    def get_history(self, obj):
        """Obtener historial de cambios desde MongoDB."""
        from core.services import audit_logger
        return audit_logger.get_history(resource_id=str(obj.id), limit=20)


class AuditEvidenceSerializer(serializers.ModelSerializer):
    """Serializer para asociaciones Audit-Evidence."""
    from .models import AuditEvidence
    
    class Meta:
        from .models import AuditEvidence
        model = AuditEvidence
        fields = [
            'id', 'audit', 'evidence',
            'created_at', 'updated_at',
            'created_by', 'updated_by',
            'deleted'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted'
        ]
