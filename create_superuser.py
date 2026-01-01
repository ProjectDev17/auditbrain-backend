import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from authentication.models import CustomUser

# Crear superusuario
user = CustomUser.objects.create_superuser(
    email='admin@auditbrain.com',
    username='admin',
    password='admin123',
    first_name='Admin',
    last_name='User'
)
print(f"Superuser created: {user.email}")

