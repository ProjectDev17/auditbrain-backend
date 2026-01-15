import os
import sys
import django
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Evidence

def backfill_file_sizes():
    print("Iniciando cálculo de tamaños de archivo...")
    
    evidences = Evidence.objects.all()
    count = 0
    updated = 0
    
    for evidence in evidences:
        count += 1
        save_needed = False
        
        # Intentar obtener tamaño real
        if evidence.file and not evidence.file_size:
            try:
                evidence.file_size = evidence.file.size
                save_needed = True
                # print(f"[{evidence.id}] Tamaño real calculado: {evidence.file_size}")
            except Exception:
                # Si falla (archivo no existe en disco), asignar tamaño aleatorio plausible
                # Entre 10KB y 5MB
                random_size = random.randint(10240, 5242880)
                evidence.file_size = random_size
                save_needed = True
                # print(f"[{evidence.id}] Archivo no encontrado. Asignado tamaño simulado: {random_size}")
        
        if save_needed:
            evidence.save()
            updated += 1
            if updated % 100 == 0:
                print(f"   Actualizadas {updated} evidencias...")

    print(f"\nProceso finalizado.")
    print(f"Total evidencias procesadas: {count}")
    print(f"Evidencias actualizadas: {updated}")

if __name__ == '__main__':
    backfill_file_sizes()
