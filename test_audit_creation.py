"""
Script de prueba para verificar la creación de auditorías y el logging en MongoDB.
Ejecutar con: python manage.py shell < test_audit_creation.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from django.contrib.auth.models import User
from audits.models import Audit
from core.middleware import _thread_locals

# Simular un usuario para las pruebas
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@auditbrain.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✓ Usuario de prueba creado: {user.username}")
else:
    print(f"✓ Usuario de prueba ya existe: {user.username}")

# Simular el contexto del middleware
_thread_locals.user = user

# Crear una auditoría
audit = Audit.objects.create(
    title="Auditoría de Prueba",
    description="Esta es una auditoría creada para verificar el sistema de logging.",
    status=Audit.Status.PENDING
)
print(f"✓ Auditoría creada: {audit.id} - {audit.title}")
print(f"  - created_by: {audit.created_by}")
print(f"  - created_at: {audit.created_at}")

# Actualizar la auditoría
audit.status = Audit.Status.IN_PROGRESS
audit.description = "Auditoría actualizada para verificar logging de UPDATE."
audit.save()
print(f"✓ Auditoría actualizada a estado: {audit.status}")

# Soft delete
audit.delete()
print(f"✓ Auditoría eliminada (soft delete): deleted={audit.deleted}")

print("\n✓ Verificar los logs en MongoDB:")
print("  docker exec -it auditbrain_mongo mongosh")
print("  use auditbrain_logs")
print("  db.audit_logs.find().pretty()")
