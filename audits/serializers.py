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
