import os
import django
import random
import uuid
from datetime import timedelta, datetime, timezone as dt_timezone
from django.utils import timezone

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auditbrain.settings")
django.setup()

from django.contrib.auth import get_user_model
from audits.models import Audit, AuditEvent, Evidence

User = get_user_model()

# --- Configuration ---
BATCH_SIZE = 2000 # Save in batches to avoid memory issues
TOTAL_RECORDS = 10000

# --- Data Pools for Coherence ---
FIRST_NAMES = ["Juan", "Maria", "Carlos", "Ana", "Luis", "Sofia", "Pedro", "Lucia", "Jorge", "Elena", "Miguel", "Paula", "David", "Carmen", "Jose", "Isabel"]
LAST_NAMES = ["Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Rivera", "Torres", "Ramirez", "Cruz", "Flores", "Gomez"]
DOMAINS = ["empresa.com", "auditcorp.net", "consulting.org", "test.io"]

AUDIT_TYPES = ["Auditoría Interna", "Revisión Financiera", "Control de Calidad", "Seguridad Informática", "Cumplimiento Legal", "Inventario Físico", "Gestión de Riesgos", "Certificación ISO"]
DEPARTMENTS = ["Finanzas", "RRHH", "IT", "Ventas", "Operaciones", "Logística", "Legal", "Marketing"]
DESCRIPTIONS = [
    "Revisión exhaustiva de los procesos del periodo.",
    "Verificación de conformidad con normativas internas.",
    "Análisis de desviaciones y planes de acción.",
    "Seguimiento a hallazgos de la auditoría anterior.",
    "Validación de controles críticos."
]

EVENT_TITLES = ["Reunión de Inicio", "Entrevista con Gerente", "Revisión de Documentación", "Inspección Ocular", "Cierre de Auditoría", "Presentación de Resultados"]
EVIDENCE_TYPES = ["pdf", "xlsx", "docx", "jpg", "png"]

# --- Helpers ---
def get_random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1).replace(tzinfo=dt_timezone.utc)
    end = datetime(end_year, 12, 31).replace(tzinfo=dt_timezone.utc)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)

def generate_users(count):
    print(f"Generando {count} usuarios...")
    users = []
    
    # Get existing emails to avoid constraint errors if running multiple times
    existing_emails = set(User.objects.values_list('email', flat=True))
    
    created_count = 0
    while created_count < count:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}.{random.randint(1000, 9999)}@{random.choice(DOMAINS)}"
        
        if email in existing_emails:
            continue
            
        users.append(User(
            first_name=first,
            last_name=last,
            email=email,
            username=email.split('@')[0],
            is_active=True,
            password="pbkdf2_sha256$260000$..." # Dummy hash for speed, won't allow login but satisfies non-null
        ))
        existing_emails.add(email)
        created_count += 1
        
        if len(users) >= BATCH_SIZE:
            User.objects.bulk_create(users, ignore_conflicts=True)
            print(f"  Insertado lote de usuarios ({created_count}/{count})")
            users = []
            
    if users:
        User.objects.bulk_create(users, ignore_conflicts=True)
        print(f"  Insertado lote final de usuarios.")

def generate_audits(count, user_ids):
    print(f"Generando {count} auditorías...")
    audits = []
    statuses = ['pending', 'in_progress', 'completed']
    
    for i in range(count):
        audit_type = random.choice(AUDIT_TYPES)
        dept = random.choice(DEPARTMENTS)
        year = random.choice([2023, 2024, 2025])
        creator_id = str(random.choice(user_ids))
        
        audits.append(Audit(
            title=f"{audit_type} - {dept} {year}",
            description=random.choice(DESCRIPTIONS),
            status=random.choice(statuses),
            created_by=creator_id,
            updated_by=creator_id,
            created_at=get_random_date()
        ))
        
        if len(audits) >= BATCH_SIZE:
            Audit.objects.bulk_create(audits)
            print(f"  Insertado lote de auditorías ({i+1}/{count})")
            audits = []
    
    if audits:
        Audit.objects.bulk_create(audits)

def generate_events(count, audit_ids, user_ids):
    print(f"Generando {count} eventos...")
    events = []
    
    for i in range(count):
        audit_id = random.choice(audit_ids)
        creator_id = str(random.choice(user_ids))
        
        events.append(AuditEvent(
            audit_id=audit_id,
            title=random.choice(EVENT_TITLES),
            description=f"Actividad programada para la auditoría.",
            event_date=get_random_date(),
            created_by=creator_id,
            updated_by=creator_id
        ))
        
        if len(events) >= BATCH_SIZE:
            AuditEvent.objects.bulk_create(events)
            print(f"  Insertado lote de eventos ({i+1}/{count})")
            events = []
            
    if events:
        AuditEvent.objects.bulk_create(events)

def generate_evidences(count, audit_ids, user_ids):
    print(f"Generando {count} evidencias...")
    evidences = []
    
    for i in range(count):
        audit_id = random.choice(audit_ids)
        creator_id = str(random.choice(user_ids))
        ext = random.choice(EVIDENCE_TYPES)
        
        evidences.append(Evidence(
            audit_id=audit_id,
            file=f"evidences/dummy/{uuid.uuid4()}.{ext}",
            file_type=ext,
            created_by=creator_id,
            updated_by=creator_id
        ))
        
        if len(evidences) >= BATCH_SIZE:
            Evidence.objects.bulk_create(evidences)
            print(f"  Insertado lote de evidencias ({i+1}/{count})")
            evidences = []
            
    if evidences:
        Evidence.objects.bulk_create(evidences)

def run():
    print("Iniciando carga de datos masiva...")
    start_time = datetime.now()

    # 1. Users
    generate_users(TOTAL_RECORDS)
    user_ids = list(User.objects.values_list('id', flat=True))
    
    # 2. Audits
    generate_audits(TOTAL_RECORDS, user_ids)
    all_audit_ids = list(Audit.objects.values_list('id', flat=True))
    
    # 3. Events
    generate_events(TOTAL_RECORDS, all_audit_ids, user_ids)
    
    # 4. Evidences
    generate_evidences(TOTAL_RECORDS, all_audit_ids, user_ids)

    end_time = datetime.now()
    print(f"Carga completada en {end_time - start_time}.")

if __name__ == "__main__":
    run()
