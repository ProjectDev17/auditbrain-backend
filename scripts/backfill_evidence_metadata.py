import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditbrain.settings')
django.setup()

from audits.models import Evidence

import random

def backfill_evidences():
    print("Iniciando backfill de metadatos de Evidencias con datos realistas...")
    
    evidences = Evidence.objects.all()
    count = 0
    updated = 0
    
    fake_titles = [
        "Informe de Auditoría Financiera 2025",
        "Evidencia de Cumplimiento Normativo",
        "Acta de Reunión de Cierre",
        "Matriz de Riesgos Actualizada",
        "Reporte de Hallazgos Preliminares",
        "Comprobante de Transacción Bancaria",
        "Políticas de Seguridad de la Información",
        "Certificado de Calidad ISO 9001",
        "Estado de Resultados Q4",
        "Dictamen del Auditor Externo",
        "Conciliación Bancaria Mensual",
        "Plan de Mitigación de Riesgos",
        "Evaluación de Control Interno",
        "Contrato de Servicios Profesionales",
        "Copia de Factura Proveedor"
    ]
    
    for evidence in evidences:
        count += 1
        
        # Asignar un título aleatorio de la lista
        new_title = random.choice(fake_titles)
        
        # Siempre actualizar para reemplazar UUIDs o nombres de archivo anteriores
        evidence.title = new_title
        evidence.description = f"Documento de soporte para la auditoría. Tipo: {evidence.file_type.upper()}. Fecha: {evidence.uploaded_at.strftime('%d/%m/%Y')}"
        
        evidence.save()
        updated += 1
        print(f"[{evidence.id}] Título actualizado a: {new_title}")

    print(f"\nProceso finalizado.")
    print(f"Total evidencias procesadas: {count}")
    print(f"Evidencias actualizadas: {updated}")

if __name__ == '__main__':
    backfill_evidences()
