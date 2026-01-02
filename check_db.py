import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from django.conf import settings
print(f"DEBUG: Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"DEBUG: Database Name: {settings.DATABASES['default']['NAME']}")

from authentication.models import CustomUser
from django.db import connection

def check_db():
    print("--- Checking DB Schema ---")
    with connection.cursor() as cursor:
        try:
            # Intentar listar columnas de customuser
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("PRAGMA table_info(authentication_customuser)")
                cols = cursor.fetchall()
                print("Columns in authentication_customuser (SQLite):")
                for col in cols:
                    print(f" - {col[1]}")
            else:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'authentication_customuser'
                """)
                cols = cursor.fetchall()
                print("Columns in authentication_customuser (Postgres):")
                for col in cols:
                    print(f" - {col[0]}")
        except Exception as e:
            print(f"Error inspecting table: {e}")

if __name__ == "__main__":
    check_db()
