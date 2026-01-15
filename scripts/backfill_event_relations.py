import os
import sys
import django
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Audit, AuditEvent

def backfill_event_relations():
    print("Iniciando redistribución de eventos en auditorías activas...")
    
    # 1. Obtener todas las auditorías activas (no eliminadas)
    active_audits = list(Audit.objects.filter(deleted=False))
    
    if not active_audits:
        print("❌ Error: No se encontraron auditorías activas. Crea al menos una antes de ejecutar.")
        return

    print(f"ℹ️  Se encontraron {len(active_audits)} auditorías activas.")
    
    # 2. Obtener todos los eventos
    events = AuditEvent.objects.all()
    count = 0
    updated = 0
    
    print(f"ℹ️  Procesando {events.count()} eventos...")

    for event in events:
        count += 1
        
        # Seleccionar una auditoría aleatoria
        random_audit = random.choice(active_audits)
        
        # Reasignar
        event.audit = random_audit
        event.save()
        
        updated += 1
        if count % 500 == 0:
            print(f"   Procesados {count} eventos...")

    print(f"\n✅ Proceso finalizado.")
    print(f"Total eventos reasignados: {updated}")
    print("Ahora los eventos están distribuidos equitativamente entre las auditorías activas.")

if __name__ == '__main__':
    backfill_event_relations()
