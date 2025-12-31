import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import Audit
from core.services import audit_logger
from core.middleware import get_current_user

@receiver(post_save, sender=Audit)
def log_audit_save(sender, instance, created, **kwargs):
    user = get_current_user()
    
    if created:
        action = 'CREATE'
    elif instance.deleted:
        action = 'DELETE'
    else:
        action = 'UPDATE'
    
    data = model_to_dict(instance)
    # Convert UUIDs specifically
    for key, value in data.items():
        if isinstance(value, uuid.UUID):
            data[key] = str(value)
            
    audit_logger.log_action(
        collection_name='Audit',
        action=action,
        data=data,
        user=user,
        resource_id=instance.id
    )

@receiver(post_delete, sender=Audit)
def log_audit_delete(sender, instance, **kwargs):
    user = get_current_user()
    data = {
        'id': str(instance.id),
        'title': instance.title
    }
    audit_logger.log_action(
        collection_name='Audit',
        action='DELETE',
        data=data,
        user=user,
        resource_id=instance.id
    )
