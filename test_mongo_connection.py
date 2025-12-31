"""
Script de diagnóstico para verificar la conexión a MongoDB.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from core.services import audit_logger

print("=== Diagnóstico de MongoDB ===")
print(f"Cliente: {audit_logger._client}")
print(f"Base de datos: {audit_logger._db}")
print(f"Colección: {audit_logger._collection}")

# Intentar escribir un log de prueba directamente
try:
    test_log = {
        'test': True,
        'message': 'Prueba de conexión directa'
    }
    result = audit_logger._collection.insert_one(test_log)
    print(f"✓ Log de prueba insertado con ID: {result.inserted_id}")
except Exception as e:
    print(f"✗ Error al insertar log de prueba: {e}")

# Verificar si hay documentos
try:
    count = audit_logger._collection.count_documents({})
    print(f"✓ Total de documentos en la colección: {count}")
except Exception as e:
    print(f"✗ Error al contar documentos: {e}")
