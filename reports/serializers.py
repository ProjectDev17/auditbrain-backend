"""
Serializers para endpoints de reportería.
Estructuran las respuestas de forma consistente y lista para gráficos.
"""
from rest_framework import serializers


class AuditSummarySerializer(serializers.Serializer):
    """Serializer para resumen general de auditorías."""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    deleted = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())


class AuditByPeriodSerializer(serializers.Serializer):
    """Serializer para auditorías agrupadas por período."""
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    grouping = serializers.CharField()


class UserProductivitySerializer(serializers.Serializer):
    """Serializer para productividad de un usuario."""
    user_id = serializers.CharField()
    user_name = serializers.CharField()
    user_email = serializers.EmailField()
    created = serializers.IntegerField()
    completed = serializers.IntegerField()


class AuditEventItemSerializer(serializers.Serializer):
    """Serializer para item de eventos por auditoría."""
    audit_id = serializers.CharField()
    audit_title = serializers.CharField()
    event_count = serializers.IntegerField()


class EventsByAuditSerializer(serializers.Serializer):
    """Serializer para resumen de eventos."""
    total_events = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    by_audit = AuditEventItemSerializer(many=True)


class EvidenceByAuditItemSerializer(serializers.Serializer):
    """Serializer para item de evidencias por auditoría."""
    audit_id = serializers.CharField()
    audit_title = serializers.CharField()
    evidence_count = serializers.IntegerField()


class EvidenceSummarySerializer(serializers.Serializer):
    """Serializer para resumen de evidencias."""
    total_evidences = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_audit = EvidenceByAuditItemSerializer(many=True)


class EventSummaryReportSerializer(serializers.Serializer):
    """Serializer para el reporte de resumen de eventos."""
    total_events = serializers.IntegerField()
    events_by_date = serializers.ListField(
        child=serializers.DictField()
    )


class ReportFilterSerializer(serializers.Serializer):
    """Serializer para validar filtros de reportes."""
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    auditor = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_null=True
    )
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed'],
        required=False,
        allow_null=True
    )
    grouping = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly'],
        default='monthly',
        required=False
    )
