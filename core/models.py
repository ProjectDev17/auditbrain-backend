import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from core.middleware import get_current_user

class TimeStampedModel(models.Model):
    """
    Modelo abstracto que añade campos created_at y updated_at.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Modelo abstracto para implementar borrado lógico.
    """
    deleted = models.BooleanField(default=False)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)
    # Podría ser UUIDField si garantizamos que el user ID es UUID, 
    # pero string es más flexible para mix de Auth sources.

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()


class AuditableModel(TimeStampedModel, SoftDeleteModel):
    """
    Modelo base para todas las entidades auditables.
    Incluye timestamps, soft delete y rastreo de usuarios.
    """
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        user_repr = str(user.id) if (user and user.is_authenticated) else 'system/anonymous'
        
        if not self.created_by:
            self.created_by = user_repr
        
        self.updated_by = user_repr
        super().save(*args, **kwargs)
