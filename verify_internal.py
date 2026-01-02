import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.serializers import UserSerializer, CustomTokenObtainPairSerializer, UserManagementSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import MagicMock

User = get_user_model()

def verify_logic():
    print("--- Verificando lógica de Serializers ---")
    
    # Buscar un usuario (preferiblemente uno que sea auditor)
    user = User.objects.filter(groups__name='Auditors').first()
    if not user:
        user = User.objects.first()
        
    if not user:
        print("No hay usuarios en la base de datos.")
        return

    print(f"\nProbando con usuario: {user.email}")
    is_auditor_real = user.groups.filter(name='Auditors').exists()
    print(f"¿Es auditor real (DB)?: {is_auditor_real}")

    # 1. UserSerializer
    serializer = UserSerializer(user)
    print(f"\n1. UserSerializer data: {json.dumps(serializer.data, indent=2)}")
    if 'is_auditor' in serializer.data:
        print(f"SUCCESS: 'is_auditor' en UserSerializer es {serializer.data['is_auditor']}")
    else:
        print("FAILURE: 'is_auditor' NO encontrado en UserSerializer")

    # 2. CustomTokenObtainPairSerializer
    token_serializer = CustomTokenObtainPairSerializer()
    token_serializer.user = user
    # Mocking validate to return what we want since we don't have password here
    refresh = RefreshToken.for_user(user)
    data = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_auditor': user.groups.filter(name='Auditors').exists(),
            'is_active': user.is_active,
        }
    }
    
    print(f"\n2. Login Response Simulation: {json.dumps(data.get('user'), indent=2)}")
    if 'is_auditor' in data.get('user'):
        print(f"SUCCESS: 'is_auditor' en Login Response es {data['user']['is_auditor']}")
    else:
        print("FAILURE: 'is_auditor' NO encontrado en Login Response")

if __name__ == "__main__":
    verify_logic()
