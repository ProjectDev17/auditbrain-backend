import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Audit
from audits.serializers import AuditSerializer

# Intentar serializar las auditorías
try:
    audits = Audit.objects.filter(deleted=False)
    print(f"Found {audits.count()} audits")
    
    serializer = AuditSerializer(audits, many=True)
    data = serializer.data
    print("Serialization successful!")
    print(f"Data: {data}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
