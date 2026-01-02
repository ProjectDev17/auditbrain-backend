import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from rest_framework.test import APIClient
from authentication.models import CustomUser

def test_api():
    print("--- API Debug ---")
    client = APIClient()
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        user = CustomUser.objects.first()
    
    if user:
        client.force_authenticate(user=user)
        print(f"Auth user: {user.email}")
    
    try:
        response = client.get('/api/users/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Server Error (500)")
            # In Django, with DEBUG=True, the response content might have the traceback
            from django.conf import settings
            if settings.DEBUG:
                print("Content sample (DEBUG=True):")
                print(response.content[:1000].decode('utf-8', errors='ignore'))
        else:
            print(f"Data: {response.json().get('results', [])[:1]}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
