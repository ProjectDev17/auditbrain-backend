import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import AuditableModel

class Audit(AuditableModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    def __str__(self):
        return f"{self.title} ({self.status})"


class AuditEvent(AuditableModel):
    """
    Modelo para eventos de calendario asociados a auditorías.
    Permite programar revisiones y fechas clave.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    event_date = models.DateTimeField()
    
    class Meta:
        ordering = ['event_date']
    
    def __str__(self):
        return f"{self.title} - {self.event_date.strftime('%Y-%m-%d')}"


class Evidence(AuditableModel):
    """
    Modelo para evidencias/archivos asociados a auditorías.
    Soporta subida de documentos con validación de tipo y tamaño.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='evidences')
    file = models.FileField(upload_to='evidences/%Y/%m/%d/')
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Evidence {self.id} - {self.audit.title}"
    
    def save(self, *args, **kwargs):
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

    class Meta:
        unique_together = ['audit', 'evidence']
        ordering = ['-created_at']

    def __str__(self):
        return f"Audit {self.audit.title} - Evidence {self.evidence.id}"
