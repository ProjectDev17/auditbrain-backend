import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from django.test import RequestFactory
from authentication.views import UserViewSet
from authentication.models import CustomUser
from rest_framework.request import Request

def debug_500():
    print("--- Debugging 500 Error in UserViewSet ---")
    factory = RequestFactory()
    request = factory.get('/api/users/')
    
    # Simular usuario autenticado
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        user = CustomUser.objects.first()
    
    view = UserViewSet.as_view({'get': 'list'})
    
    # Adaptar request para DRF
    from rest_framework.test import force_authenticate
    
    try:
        # Usar APIRequestFactory mejor
        from rest_framework.test import APIRequestFactory
        ar_factory = APIRequestFactory()
        ar_request = ar_factory.get('/api/users/')
        if user:
            force_authenticate(ar_request, user=user)
        
        response = view(ar_request)
        print(f"Status Code: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error detail: {response.data}")
        else:
            print(f"Response data sample: {str(response.data)[:200]}...")
    except Exception as e:
        print("\n--- TRACEBACK ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_500()
