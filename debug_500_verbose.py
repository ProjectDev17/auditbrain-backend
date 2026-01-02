import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from django.test import RequestFactory
from authentication.views import UserViewSet
from authentication.models import CustomUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

def debug_500():
    print("--- Debugging 500 Error in UserViewSet (Verbose) ---")
    ar_factory = APIRequestFactory()
    ar_request = ar_factory.get('/api/users/')
    
    # Simular usuario autenticado (superusuario para evitar problemas de permisos)
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        user = CustomUser.objects.first()
    
    if user:
        print(f"Authenticating as: {user.email}")
        force_authenticate(ar_request, user=user)
    else:
        print("No users found to authenticate with!")

    view = UserViewSet.as_view({'get': 'list'})
    
    try:
        response = view(ar_request)
        print(f"Status Code: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error data: {response.data}")
            # Si es un dict y tiene 'detail', imprimirlo
            if isinstance(response.data, dict) and 'detail' in response.data:
                print(f"Detail: {response.data['detail']}")
        else:
            print("Success! Data sample:")
            print(json.dumps(response.data, indent=2)[:500])
    except Exception as e:
        print("\n--- CRITICAL ERROR DURING VIEW EXECUTION ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import json
    debug_500()
