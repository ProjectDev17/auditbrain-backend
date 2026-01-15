import os
import sys
import django
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Audit, Evidence

def backfill_relations():
    print("Iniciando distribución de evidencias en auditorías existentes...")
    
    # 1. Obtener todas las auditorías disponibles
    audits = list(Audit.objects.filter(deleted=False))
    
    if not audits:
        print("❌ Error: No se encontraron auditorías. Por favor crea al menos una auditoría antes de ejecutar este script.")
        return

    print(f"ℹ️  Se encontraron {len(audits)} auditorías disponibles.")
    
    # 2. Obtener todas las evidencias
    evidences = Evidence.objects.all()
    count = 0
    updated = 0
    
    print(f"ℹ️  Procesando {evidences.count()} evidencias...")

    for evidence in evidences:
        count += 1
        
        # Seleccionar una auditoría aleatoria
        random_audit = random.choice(audits)
        
        # Asignar (o reasignar)
        evidence.audit = random_audit
        evidence.save()
        
        updated += 1
        if count % 100 == 0:
            print(f"   Procesadas {count} evidencias...")

    print(f"\n✅ Proceso finalizado.")
    print(f"Total evidencias reasignadas: {updated}")
    print("Ahora las evidencias están distribuidas entre tus auditorías.")

if __name__ == '__main__':
    backfill_relations()
