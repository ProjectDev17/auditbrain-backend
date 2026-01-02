"""
Servicios de agregación y utilidades para reportería.
Centraliza la lógica de negocio para cálculos y agregaciones de datos.
"""
import datetime as dt
from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from audits.models import Audit, AuditEvent, Evidence
from authentication.models import CustomUser
from core.services import audit_logger


def apply_report_filters(queryset, filters, date_field='created_at'):
    """
    Aplica filtros comunes de reportería a un queryset.
    """
    if not filters:
        return queryset
    
    # Filtros de fecha
    start_date = filters.get('start_date')
    if start_date:
        if isinstance(start_date, str):
            start_date = dt.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Si es un objeto date puro (pero no datetime), convertir a datetime
        if isinstance(start_date, dt.date) and not isinstance(start_date, dt.datetime):
            start_date = dt.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
            if timezone.is_aware(timezone.now()):
                start_date = timezone.make_aware(start_date)
        
        queryset = queryset.filter(**{f"{date_field}__gte": start_date})
    
    end_date = filters.get('end_date')
    if end_date:
        if isinstance(end_date, str):
            end_date = dt.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Si es un objeto date puro (pero no datetime), convertir a datetime
        if isinstance(end_date, dt.date) and not isinstance(end_date, dt.datetime):
            end_date = dt.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)
            if timezone.is_aware(timezone.now()):
                end_date = timezone.make_aware(end_date)
            
        queryset = queryset.filter(**{f"{date_field}__lte": end_date})
    
    # Filtro de auditor (usuario asignado)
    auditor_id = filters.get('auditor') or filters.get('user_id')
    if auditor_id:
        # Si es AuditEvent o Evidence, el auditor está en audit__auditor
        if queryset.model in [AuditEvent, Evidence]:
            queryset = queryset.filter(audit__auditor_id=auditor_id)
        else:
            queryset = queryset.filter(auditor_id=auditor_id)
            
    # Filtro de estado
    status = filters.get('status')
    if status:
        if queryset.model in [AuditEvent, Evidence]:
            queryset = queryset.filter(audit__status=status)
        else:
            queryset = queryset.filter(status=status)
            
    return queryset


def get_audit_summary(filters=None):
    """
    Obtiene resumen general de auditorías.
    
    Returns:
        dict: Diccionario con totales y conteos por estado
    """
    queryset = Audit.objects.all()
    queryset = apply_report_filters(queryset, filters)
    
    total = queryset.count()
    active = queryset.filter(deleted=False).count()
    deleted = queryset.filter(deleted=True).count()
    
    by_status = {}
    for status_choice in Audit.Status.choices:
        status_key = status_choice[0]
        count = queryset.filter(status=status_key, deleted=False).count()
        by_status[status_key] = count
    
    return {
        'total': total,
        'active': active,
        'deleted': deleted,
        'by_status': by_status
    }


def get_audits_by_period(filters=None):
    """
    Obtiene auditorías agrupadas por período temporal.
    
    Returns:
        dict: Diccionario con labels y data para gráficos
    """
    queryset = Audit.objects.filter(deleted=False)
    
    # Aplicar filtros
    queryset = apply_report_filters(queryset, filters)
    
    grouping = filters.get('grouping', 'monthly') if filters else 'monthly'
    
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


def get_audits_by_user(filters=None):
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


def get_events_by_audit(filters=None):
    """
    Obtiene resumen de eventos por auditoría.
    
    Returns:
        dict: Diccionario con totales y eventos próximos
    """
    now = timezone.now()
    
    queryset = AuditEvent.objects.filter(deleted=False)
    queryset = apply_report_filters(queryset, filters, date_field='event_date')
    
    total_events = queryset.count()
    upcoming_events = queryset.filter(event_date__gte=now).count()
    
    # Eventos por auditoría
    by_audit = (
        queryset
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


def get_evidence_summary(filters=None):
    """
    Obtiene resumen de evidencias.
    
    Returns:
        dict: Diccionario con totales por tipo y por auditoría
    """
    queryset = Evidence.objects.filter(deleted=False)
    queryset = apply_report_filters(queryset, filters)
    
    total_evidences = queryset.count()
    
    # Evidencias por tipo de archivo
    by_type = (
        queryset
        .values('file_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    by_type_dict = {item['file_type']: item['count'] for item in by_type}
    
    # Evidencias por auditoría
    by_audit = (
        queryset
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


def get_event_summary_report(filters=None):
    """
    Obtiene reporte resumen de eventos, incluyendo distribución por fecha.
    
    Returns:
        dict: Totales y desglose por fecha
    """
    queryset = AuditEvent.objects.filter(deleted=False)
    
    # Si no hay filtros de fecha, mostrar últimos 30 días por defecto
    if not filters or (not filters.get('start_date') and not filters.get('end_date')):
        default_start = timezone.now() - dt.timedelta(days=30)
        queryset = queryset.filter(event_date__gte=default_start)
    
    # Aplicar filtros adicionales de la request
    queryset = apply_report_filters(queryset, filters, date_field='event_date')
    
    total_events = queryset.count()
    
    # Agrupar por fecha usando el queryset ya filtrado
    events_by_date = (
        queryset
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
    import uuid
    # Asegurar que los filtros son serializables (convertir UUIDs a string)
    serializable_filters = {}
    if filters:
        for key, value in filters.items():
            if isinstance(value, uuid.UUID):
                serializable_filters[key] = str(value)
            elif isinstance(value, (dt.datetime, dt.date, dt.timedelta)):
                serializable_filters[key] = str(value)
            else:
                serializable_filters[key] = value

    audit_logger.log_action(
        collection_name='Report',
        action='QUERY',
        data={
            'report_type': report_type,
            'filters': serializable_filters,
            'execution_time_ms': execution_time_ms
        },
        user=user
    )
