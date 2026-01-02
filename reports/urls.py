"""
URLs para endpoints de reportería.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Resumen general de auditorías
    path('audits/summary/', views.AuditSummaryView.as_view(), name='audit-summary'),
    
    # Auditorías por período
    path('audits/by-period/', views.AuditByPeriodView.as_view(), name='audit-by-period'),
    
    # Productividad por auditor
    path('audits/by-user/', views.AuditByUserView.as_view(), name='audit-by-user'),
    
    # Eventos por auditoría
    path('events/by-audit/', views.EventsByAuditView.as_view(), name='events-by-audit'),
    
    # Resumen de evidencias
    path('evidences/summary/', views.EvidenceSummaryView.as_view(), name='evidence-summary'),
    
    # Resumen de eventos
    path('events/summary/', views.EventSummaryView.as_view(), name='event-summary'),
]
