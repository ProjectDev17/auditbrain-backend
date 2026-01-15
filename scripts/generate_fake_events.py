import os
import sys
import django
import random
import time
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Audit, AuditEvent

def generate_fake_events():
    TOTAL_EVENTS = 2_000_000
    BATCH_SIZE = 5000
    
    print(f"🚀 Iniciando generación masiva de {TOTAL_EVENTS} eventos...")
    print(f"📦 Tamaño de lote (BATCH_SIZE): {BATCH_SIZE}")

    # 1. Obtener auditorías activas
    audits = list(Audit.objects.filter(deleted=False).values_list('id', flat=True))
    
    if not audits:
        print("❌ Error: No se encontraron auditorías activas.")
        return

    print(f"ℹ️  Distribuyendo sobre {len(audits)} auditorías.")

    # Datos fake para aleatorizar
    titles = [
        "Reunión de seguimiento semanal", "Revisión de hallazgos críticos", 
        "Entrevista con Gerente Financiero", "Inspección física de inventario",
        "Validación de controles TI", "Prueba de recorrido (Walkthrough)",
        "Análisis de variaciones presupuestales", "Confirmación de saldos bancarios",
        "Revisión de actas de comité", "Evaluación de cumplimiento normativo",
        "Cierre de auditoría preliminar", "Presentación de informe borrador",
        "Discusión de plan de acción", "Verificación de correcciones"
    ]
    
    descriptions = [
        "Se revisaron los documentos solicitados y se validaron las firmas.",
        "Reunión realizada vía Teams con el equipo de contabilidad.",
        "Se encontraron discrepancias menores que fueron notificadas.",
        "El proceso cumple con los estándares establecidos en la política interna.",
        "Pendiente recibir la evidencia de soporte para este punto.",
        "Sin novedades que reportar en esta sesión.",
        "Se requiere seguimiento adicional la próxima semana."
    ]
    
    event_types = ['meeting', 'milestone', 'task', 'finding', 'other']  # Ajustar según choices reales
    severities = ['low', 'medium', 'high', 'critical']

    start_time = time.time()
    events_created = 0
    batch = []

    # Fecha base para random
    base_date = timezone.now() - timedelta(days=365)

    for i in range(TOTAL_EVENTS):
        # Generar datos aleatorios
        audit_id = random.choice(audits)
        title = random.choice(titles)
        days_offset = random.randint(0, 365)
        occurred_at = base_date + timedelta(days=days_offset)
        
        event = AuditEvent(
            audit_id=audit_id,
            title=f"{title} - {random.randint(1000, 9999)}", # Hacer título único/variado
            description=random.choice(descriptions),
            event_type=random.choice(event_types),
            severity=random.choice(severities),
            occurred_at=occurred_at,
            created_by="system-script"
        )
        batch.append(event)
        
        if len(batch) >= BATCH_SIZE:
            AuditEvent.objects.bulk_create(batch)
            events_created += len(batch)
            batch = []
            
            # Progreso
            elapsed = time.time() - start_time
            rate = events_created / elapsed if elapsed > 0 else 0
            if (events_created % (BATCH_SIZE * 10)) == 0:
                print(f"   ✅ {events_created} eventos creados... ({rate:.0f} ev/s)")

    # Insertar remanente
    if batch:
        AuditEvent.objects.bulk_create(batch)
        events_created += len(batch)

    total_time = time.time() - start_time
    print(f"\n✨ Generación completada exitosamente.")
    print(f"   Total eventos: {events_created}")
    print(f"   Tiempo total: {total_time:.2f} segundos")
    print(f"   Promedio: {events_created / total_time:.0f} ev/s")

if __name__ == '__main__':
    generate_fake_events()
