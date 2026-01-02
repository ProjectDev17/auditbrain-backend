"""
Servicios de agregación y utilidades para reportería.
Centraliza la lógica de negocio para cálculos y agregaciones de datos.
"""
from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from audits.models import Audit, AuditEvent, Evidence
from authentication.models import CustomUser
from core.services import audit_logger


def get_audit_summary():
    """
    Obtiene resumen general de auditorías.
    
    Returns:
        dict: Diccionario con totales y conteos por estado
    """
    total = Audit.objects.count()
    active = Audit.objects.filter(deleted=False).count()
    deleted = Audit.objects.filter(deleted=True).count()
    
    by_status = {}
    for status_choice in Audit.Status.choices:
        status_key = status_choice[0]
        count = Audit.objects.filter(status=status_key, deleted=False).count()
        by_status[status_key] = count
    
    return {
        'total': total,
        'active': active,
        'deleted': deleted,
        'by_status': by_status
    }


def get_audits_by_period(start_date=None, end_date=None, grouping='monthly'):
    """
    Obtiene auditorías agrupadas por período temporal.
    
    Args:
        start_date: Fecha de inicio (datetime o string ISO)
        end_date: Fecha de fin (datetime o string ISO)
        grouping: Tipo de agrupación ('daily', 'weekly', 'monthly')
    
    Returns:
        dict: Diccionario con labels y data para gráficos
    """
    queryset = Audit.objects.filter(deleted=False)
    
    # Aplicar filtros de fecha
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        queryset = queryset.filter(created_at__gte=start_date)
    
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        queryset = queryset.filter(created_at__lte=end_date)
    
    # Seleccionar función de truncado según agrupación
    if grouping == 'daily':
        trunc_func = TruncDate
        date_format = '%Y-%m-%d'
    elif grouping == 'weekly':
        trunc_func = TruncWeek
        date_format = '%Y-W%W'
    else:  # monthly
        trunc_func = TruncMonth
        date_format = '%Y-%m'
    
    # Agrupar y contar
    results = (
        queryset
        .annotate(period=trunc_func('created_at'))
        .values('period')
        .annotate(count=Count('id'))
        .order_by('period')
    )
    
    labels = []
    data = []
    for result in results:
        period_date = result['period']
        if grouping == 'weekly':
            # Para semanal, formatear como año-semana
            labels.append(period_date.strftime(date_format))
        else:
            labels.append(period_date.strftime(date_format))
        data.append(result['count'])
    
    return {
        'labels': labels,
        'data': data,
        'grouping': grouping
    }


def get_audits_by_user():
    """
    Obtiene productividad por auditor (usuario).
    
    Returns:
        list: Lista de diccionarios con información de cada usuario
    """
    users = CustomUser.objects.filter(is_active=True)
    
    results = []
    for user in users:
        user_id_str = str(user.id)
        
        created_count = Audit.objects.filter(
            created_by=user_id_str,
            deleted=False
        ).count()
        
        completed_count = Audit.objects.filter(
            created_by=user_id_str,
            status=Audit.Status.COMPLETED,
            deleted=False
        ).count()
        
        # Solo incluir usuarios con auditorías
        if created_count > 0:
            results.append({
                'user_id': str(user.id),
                'user_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'user_email': user.email,
                'created': created_count,
                'completed': completed_count
            })
    
    # Ordenar por auditorías creadas (descendente)
    results.sort(key=lambda x: x['created'], reverse=True)
    
    return results


def get_events_by_audit():
    """
    Obtiene resumen de eventos por auditoría.
    
    Returns:
        dict: Diccionario con totales y eventos próximos
    """
    now = timezone.now()
    
    total_events = AuditEvent.objects.filter(deleted=False).count()
    upcoming_events = AuditEvent.objects.filter(
        deleted=False,
        event_date__gte=now
    ).count()
    
    # Eventos por auditoría
    by_audit = (
        AuditEvent.objects
        .filter(deleted=False)
        .values('audit__id', 'audit__title')
        .annotate(event_count=Count('id'))
        .order_by('-event_count')
    )
    
    by_audit_list = [
        {
            'audit_id': str(item['audit__id']),
            'audit_title': item['audit__title'],
            'event_count': item['event_count']
        }
        for item in by_audit
    ]
    
    return {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'by_audit': by_audit_list
    }


def get_evidence_summary():
    """
    Obtiene resumen de evidencias.
    
    Returns:
        dict: Diccionario con totales por tipo y por auditoría
    """
    total_evidences = Evidence.objects.filter(deleted=False).count()
    
    # Evidencias por tipo de archivo
    by_type = (
        Evidence.objects
        .filter(deleted=False)
        .values('file_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    by_type_dict = {item['file_type']: item['count'] for item in by_type}
    
    # Evidencias por auditoría
    by_audit = (
        Evidence.objects
        .filter(deleted=False)
        .values('audit__id', 'audit__title')
        .annotate(evidence_count=Count('id'))
        .order_by('-evidence_count')
    )
    
    by_audit_list = [
        {
            'audit_id': str(item['audit__id']),
            'audit_title': item['audit__title'],
            'evidence_count': item['evidence_count']
        }
        for item in by_audit
    ]
    
    return {
        'total_evidences': total_evidences,
        'by_type': by_type_dict,
        'by_audit': by_audit_list
    }


def get_event_summary_report(days=30):
    """
    Obtiene reporte resumen de eventos, incluyendo distribución por fecha.
    
    Args:
        days: Número de días hacia atrás para analizar (default: 30)
        
    Returns:
        dict: Totales y desglose por fecha
    """
    queryset = AuditEvent.objects.filter(deleted=False)
    total_events = queryset.count()
    
    # Calcular fecha de inicio
    start_date = timezone.now() - timedelta(days=days)
    
    # Agrupar por fecha
    events_by_date = (
        queryset
        .filter(event_date__gte=start_date)
        .annotate(date=TruncDate('event_date'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    # Formatear resultados
    by_date_list = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        }
        for item in events_by_date
        if item['date']  # Filtrar posibles nulos
    ]
    
    # Llenar huecos de fechas (opcional, pero recomendado para gráficos)
    # Por ahora devolvemos solo las fechas con datos para simplificar
    
    return {
        'total_events': total_events,
        'events_by_date': by_date_list
    }


def log_report_query(report_type, filters, execution_time_ms, user=None):
    """
    Registra una consulta de reportería en MongoDB.
    
    Args:
        report_type: Tipo de reporte ejecutado
        filters: Diccionario con filtros aplicados
        execution_time_ms: Tiempo de ejecución en milisegundos
        user: Usuario que ejecutó la consulta
    """
    audit_logger.log_action(
        collection_name='Report',
        action='QUERY',
        data={
            'report_type': report_type,
            'filters': filters,
            'execution_time_ms': execution_time_ms
        },
        user=user
    )
