"""
Views para endpoints de reportería.
Proveen datos agregados listos para dashboards.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from time import time

from . import services
from . import serializers


class AuditSummaryView(APIView):
    """
    Endpoint para resumen general de auditorías.
    
    GET /api/reports/audits/summary/
    
    Retorna:
    - Total de auditorías
    - Auditorías activas vs eliminadas
    - Auditorías por estado
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Obtener datos
        data = services.get_audit_summary()
        
        # Serializar respuesta
        serializer = serializers.AuditSummarySerializer(data)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='audit_summary',
            filters={},
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)


class AuditByPeriodView(APIView):
    """
    Endpoint para auditorías agrupadas por período.
    
    GET /api/reports/audits/by-period/
    
    Query params:
    - start_date: Fecha de inicio (ISO format)
    - end_date: Fecha de fin (ISO format)
    - grouping: daily, weekly, monthly (default: monthly)
    
    Retorna datos listos para gráficos de líneas/barras.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Validar filtros
        filter_serializer = serializers.ReportFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(
                filter_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        filters = filter_serializer.validated_data
        
        # Obtener datos
        data = services.get_audits_by_period(
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            grouping=filters.get('grouping', 'monthly')
        )
        
        # Serializar respuesta
        serializer = serializers.AuditByPeriodSerializer(data)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='audit_by_period',
            filters=filters,
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)


class AuditByUserView(APIView):
    """
    Endpoint para productividad por auditor.
    
    GET /api/reports/audits/by-user/
    
    Retorna lista de usuarios con:
    - Auditorías creadas
    - Auditorías completadas
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Obtener datos
        data = services.get_audits_by_user()
        
        # Serializar respuesta
        serializer = serializers.UserProductivitySerializer(data, many=True)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='audit_by_user',
            filters={},
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)


class EventsByAuditView(APIView):
    """
    Endpoint para resumen de eventos.
    
    GET /api/reports/events/by-audit/
    
    Retorna:
    - Total de eventos
    - Eventos próximos
    - Eventos por auditoría
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Obtener datos
        data = services.get_events_by_audit()
        
        # Serializar respuesta
        serializer = serializers.EventsByAuditSerializer(data)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='events_by_audit',
            filters={},
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)


class EvidenceSummaryView(APIView):
    """
    Endpoint para resumen de evidencias.
    
    GET /api/reports/evidences/summary/
    
    Retorna:
    - Total de evidencias
    - Evidencias por tipo de archivo
    - Evidencias por auditoría
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Obtener datos
        data = services.get_evidence_summary()
        
        # Serializar respuesta
        serializer = serializers.EvidenceSummarySerializer(data)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='evidence_summary',
            filters={},
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)


class EventSummaryView(APIView):
    """
    Endpoint para reporte resumen de eventos.
    
    GET /api/reports/events/summary/
    
    Retorna:
    - Total de eventos
    - Historial de eventos por día (últimos 30 días)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_time = time()
        
        # Obtener datos (últimos 30 días por defecto)
        data = services.get_event_summary_report(days=30)
        
        # Serializar respuesta
        serializer = serializers.EventSummaryReportSerializer(data)
        
        # Registrar consulta
        execution_time = int((time() - start_time) * 1000)
        services.log_report_query(
            report_type='event_summary_report',
            filters={'days': 30},
            execution_time_ms=execution_time,
            user=request.user
        )
        
        return Response(serializer.data)
