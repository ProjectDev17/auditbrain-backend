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


# Signals para AuditEvent
@receiver(post_save, sender=Audit.events.rel.related_model)
def log_event_save(sender, instance, created, **kwargs):
    user = get_current_user()
    action = 'CREATE_EVENT' if created else 'UPDATE_EVENT'
    
    audit_logger.log_action(
        collection_name='AuditEvent',
        action=action,
        data={
            'event_id': str(instance.id),
            'audit_id': str(instance.audit_id),
            'title': instance.title,
            'event_date': instance.event_date.isoformat()
        },
        user=user,
        resource_id=instance.audit_id
    )


@receiver(post_delete, sender=Audit.events.rel.related_model)
def log_event_delete(sender, instance, **kwargs):
    user = get_current_user()
    audit_logger.log_action(
        collection_name='AuditEvent',
        action='DELETE_EVENT',
        data={
            'event_id': str(instance.id),
            'title': instance.title
        },
        user=user,
        resource_id=instance.audit_id
    )


# Signals para Evidence
@receiver(post_save, sender=Audit.evidences.rel.related_model)
def log_evidence_upload(sender, instance, created, **kwargs):
    if created:
        user = get_current_user()
        audit_logger.log_action(
            collection_name='Evidence',
            action='UPLOAD_EVIDENCE',
            data={
                'evidence_id': str(instance.id),
                'file_type': instance.file_type,
                'file_name': instance.file.name
            },
            user=user,
            resource_id=instance.audit_id
        )


@receiver(post_delete, sender=Audit.evidences.rel.related_model)
def log_evidence_delete(sender, instance, **kwargs):
    user = get_current_user()
    audit_logger.log_action(
        collection_name='Evidence',
        action='DELETE_EVIDENCE',
        data={
            'evidence_id': str(instance.id),
            'file_type': instance.file_type
        },
        user=user,
        resource_id=instance.audit_id
    )
