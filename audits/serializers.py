from rest_framework import serializers
from django.utils import timezone
from .models import Audit, AuditType, AuditEvent, Evidence, AuditEvidence
import re


class AuditTypeSerializer(serializers.ModelSerializer):
    """Serializer para tipos de auditoría."""
    class Meta:
        model = AuditType
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'deleted']
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted']


class AuditSerializer(serializers.ModelSerializer):
    # Display fields for frontend (read-only)
    auditor_name = serializers.SerializerMethodField()
    audit_type_name = serializers.CharField(source='audit_type.name', read_only=True)
    
    class Meta:
        model = Audit
        fields = [
            'id', 'title', 'description', 'status',
            'audit_type', 'audit_type_name',
            'auditor', 'auditor_name',
            'start_date', 'end_date',
            'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted', 'deleted_by',
            'auditor_name', 'audit_type_name'
        ]
    
    def get_auditor_name(self, obj):
        """Return auditor's full name or username if available."""
        if obj.auditor:
            full_name = obj.auditor.get_full_name()
            return full_name if full_name else obj.auditor.username
        return None
    
    def validate_title(self, value):
        """Validar título: longitud, contenido HTML y caracteres válidos."""
        clean_value = value.strip()
        
        if len(clean_value) < 5:
            raise serializers.ValidationError("El título debe tener al menos 5 caracteres.")
            
        # Validar HTML tags
        if re.search(r'<[^>]+>', clean_value):
            raise serializers.ValidationError("El título no puede contener etiquetas HTML.")
            
        # Validar que tenga contenido alfanumérico real
        if not re.search(r'[a-zA-Z0-9]', clean_value):
            raise serializers.ValidationError("El título debe contener caracteres alfanuméricos.")
            
        return clean_value
    
    def validate(self, data):
        """Validaciones a nivel de objeto."""
        # 1. Validaciones para edición
        if self.instance and self.instance.deleted:
            raise serializers.ValidationError("No se puede modificar una auditoría eliminada.")
        
        # 2. Validar Fechas
        start_date = data.get('start_date', self.instance.start_date if self.instance else None)
        end_date = data.get('end_date', self.instance.end_date if self.instance else None)
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': "La fecha de fin no puede ser anterior a la de inicio."
            })
            
        # Fecha en el pasado (solo para creación)
        if not self.instance and start_date and start_date < timezone.now().date():
             raise serializers.ValidationError({
                'start_date': "La fecha de inicio no puede ser en el pasado."
            })

        # 3. Validar Integridad Referencial
        audit_type = data.get('audit_type')
        if audit_type and audit_type.deleted:
             raise serializers.ValidationError({'audit_type': "El tipo de auditoría seleccionado no es válido."})
             
        auditor = data.get('auditor')
        if auditor and not auditor.is_active:
             raise serializers.ValidationError({'auditor': "El auditor asignado no es un usuario activo."})

        # 4. Validar Duplicados (Mismo Título + Tipo + Activa)
        title = data.get('title')
        audit_type_val = data.get('audit_type')
        
        # Si es edición, completar datos faltantes con la instancia actual
        if self.instance:
            title = title or self.instance.title
            audit_type_val = audit_type_val or self.instance.audit_type

        if title and audit_type_val:
            qs = Audit.objects.filter(
                title__iexact=title, 
                audit_type=audit_type_val, 
                deleted=False
            )
            
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            
            if qs.exists():
                raise serializers.ValidationError({
                    'non_field_errors': "Ya existe una auditoría activa con ese título y tipo."
                })

        # 5. Validar transiciones de estado
        if self.instance:
            current_status = self.instance.status
            new_status = data.get('status', current_status)
            
            if current_status == Audit.Status.COMPLETED and new_status == Audit.Status.PENDING:
                raise serializers.ValidationError({
                    'status': "No se puede cambiar de 'completed' a 'pending'."
                })
            
            if current_status == Audit.Status.COMPLETED and new_status == Audit.Status.IN_PROGRESS:
                raise serializers.ValidationError({
                    'status': "No se puede cambiar de 'completed' a 'in_progress'."
                })
        
        return data


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de calendario de auditorías."""
    
    class Meta:
        model = AuditEvent
        fields = [
            'id', 'title', 'description', 
            'event_type', 'severity', 'occurred_at',
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
    
    def validate_title(self, value):
        """Validar título."""
        clean_value = value.strip()
        if len(clean_value) < 3:
            raise serializers.ValidationError("El título debe tener al menos 3 caracteres.")
        
        if re.search(r'<[^>]+>', clean_value):
            raise serializers.ValidationError("El título no puede contener etiquetas HTML.")
            
        return clean_value

    def validate(self, data):
        # Validar fechas dentro del rango de la auditoría
        audit_id = self.context.get('audit_id') or (self.instance.audit_id if self.instance else None)
        # Nota: Normalmente el audit_id viaja en el context desde el ViewSet o se infiere
        
        # Validar unicidad (mismo título, misma fecha, misma auditoría)
        title = data.get('title')
        occurred_at = data.get('occurred_at')
        
        if title and occurred_at and audit_id:
            qs = self.Meta.model.objects.filter(
                audit_id=audit_id,
                title__iexact=title,
                occurred_at=occurred_at,
                deleted=False
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
                
            if qs.exists():
                raise serializers.ValidationError("Ya existe un evento con este título y fecha para esta auditoría.")

        return data


class EvidenceSerializer(serializers.ModelSerializer):
    """Serializer para evidencias/archivos de auditorías."""
    
    ALLOWED_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx', 'txt', 'csv']
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    class Meta:
        model = Evidence
        fields = [
            'id', 'audit', 'title', 'description', 'file', 'file_type', 'file_size', 'uploaded_at',
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
        read_only_fields = [
            'id', 'file_type', 'file_size', 'uploaded_at', 
            'created_at', 'created_by', 'updated_at', 'updated_by'
        ]
    
    def validate_file(self, value):
        """Validar archivo: tipo, tamaño y nombre seguro."""
        # 1. Validar extensión
        ext = value.name.split('.')[-1].lower()
        if ext not in self.ALLOWED_TYPES:
            raise serializers.ValidationError(
                f"Tipo de archivo no permitido. Permitidos: {', '.join(self.ALLOWED_TYPES)}"
            )
        
        # 2. Validar tamaño
        if value.size > self.MAX_SIZE:
            raise serializers.ValidationError("El archivo no puede superar 10MB.")
            
        # 3. Validar Nombre seguro (Regex)
        # Solo permitir letras, números, puntos, guiones y guiones bajos
        if not re.match(r'^[a-zA-Z0-9._ -]+$', value.name):
            raise serializers.ValidationError(
                "El nombre del archivo contiene caracteres inválidos. Use solo letras, números, guiones y espacios."
            )
            
        # 4. Validar doble extensión (check simple)
        if value.name.count('.') > 1:
            # Permitir si es algo comun como .tar.gz (aunque no esta en allowed types), pero bloquear .php.jpg
            # Para esta lista whitelist, bloqueamos todo lo que tenga doble punto para máxima seguridad
            raise serializers.ValidationError("El nombre del archivo no puede tener múltiples extensiones.")
        
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
            'id', 'audit', 'evidence', 'description',
            'created_at', 'updated_at',
            'created_by', 'updated_by',
            'deleted'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted'
        ]
