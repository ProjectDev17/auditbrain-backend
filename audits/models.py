import uuid
from typing import Optional
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import AuditableModel


class AuditType(AuditableModel):
    """Tipo de auditoría."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return str(self.name)


class Audit(AuditableModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        PLANNED = 'planned', _('Planned')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    audit_type = models.ForeignKey(
        AuditType, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits'
    )
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['start_date']),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"


class AuditEvent(AuditableModel):
    """
    Modelo para eventos de calendario asociados a auditorías.
    Permite programar revisiones y fechas clave.
    """
    class EventType(models.TextChoices):
        FINDING = 'finding', _('Finding')
        RECOMMENDATION = 'recommendation', _('Recommendation')
        OBSERVATION = 'observation', _('Observation')
        MEETING = 'meeting', _('Meeting')
        MILESTONE = 'milestone', _('Milestone')
        OTHER = 'other', _('Other')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        blank=True,
        null=True
    )
    occurred_at = models.DateTimeField()
    
    class Meta:
        ordering = ['occurred_at']
    
    def __str__(self) -> str:
        return f"{self.title} - {self.occurred_at.strftime('%Y-%m-%d')}"




class Evidence(AuditableModel):
    """
    Modelo para evidencias/archivos asociados a auditorías.
    Soporta subida de documentos con validación de tipo y tamaño.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='evidences')
    title = models.CharField(max_length=255, default="Evidencia sin título")
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='evidences/%Y/%m/%d/')
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self) -> str:
        return f"Evidence {self.id} - {self.audit.title}"
    
    def save(self, *args, **kwargs) -> None:
        # Extraer tipo de archivo del nombre
        if self.file and not self.file_type:
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)


class AuditEvidence(AuditableModel):
    """
    Modelo intermedio para asociar evidencias con auditorías.
    Permite relación muchos-a-muchos con metadatos de auditoría.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='audit_evidences')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='audit_evidences')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Descripción del archivo')

    class Meta:
        unique_together = ['audit', 'evidence']
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Audit {self.audit.title} - Evidence {self.evidence.id}"
