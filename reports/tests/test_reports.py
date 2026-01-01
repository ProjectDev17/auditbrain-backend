"""
Tests para endpoints de reportería.
Valida agregaciones, filtros y performance.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from unittest.mock import patch
from time import time

from audits.models import Audit, AuditEvent, Evidence
from reports import services

User = get_user_model()


class ReportAggregationTests(TestCase):
    """Tests para validar agregaciones de datos."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Crear auditorías de prueba con diferentes estados
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            
            # 5 pending
            for i in range(5):
                Audit.objects.create(
                    title=f'Audit Pending {i}',
                    status=Audit.Status.PENDING
                )
            
            # 3 in_progress
            for i in range(3):
                Audit.objects.create(
                    title=f'Audit In Progress {i}',
                    status=Audit.Status.IN_PROGRESS
                )
            
            # 2 completed
            for i in range(2):
                Audit.objects.create(
                    title=f'Audit Completed {i}',
                    status=Audit.Status.COMPLETED
                )
            
            # 1 deleted
            deleted_audit = Audit.objects.create(
                title='Audit Deleted',
                status=Audit.Status.PENDING
            )
            deleted_audit.delete()
    
    def test_audit_summary(self):
        """Test resumen general de auditorías."""
        summary = services.get_audit_summary()
        
        self.assertEqual(summary['total'], 11)
        self.assertEqual(summary['active'], 10)
        self.assertEqual(summary['deleted'], 1)
        self.assertEqual(summary['by_status']['pending'], 5)
        self.assertEqual(summary['by_status']['in_progress'], 3)
        self.assertEqual(summary['by_status']['completed'], 2)
    
    def test_audits_by_period_monthly(self):
        """Test agrupación por período mensual."""
        result = services.get_audits_by_period(grouping='monthly')
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        self.assertEqual(result['grouping'], 'monthly')
        self.assertTrue(len(result['labels']) > 0)
        self.assertEqual(len(result['labels']), len(result['data']))
    
    def test_audits_by_user(self):
        """Test productividad por usuario."""
        results = services.get_audits_by_user()
        
        self.assertTrue(len(results) > 0)
        user_data = results[0]
        
        self.assertIn('user_id', user_data)
        self.assertIn('user_name', user_data)
        self.assertIn('user_email', user_data)
        self.assertIn('created', user_data)
        self.assertIn('completed', user_data)
        
        # Verificar conteos
        self.assertEqual(user_data['created'], 10)  # No cuenta deleted
        self.assertEqual(user_data['completed'], 2)


class ReportFilterTests(TestCase):
    """Tests para validar filtros de reportes."""
    
    def setUp(self):
        """Configurar datos de prueba con fechas específicas."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        now = timezone.now()
        
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            
            # Auditorías de este mes
            for i in range(3):
                audit = Audit.objects.create(title=f'Current Month {i}')
                audit.created_at = now
                audit.save()
            
            # Auditorías del mes pasado
            for i in range(2):
                audit = Audit.objects.create(title=f'Last Month {i}')
                audit.created_at = now - timedelta(days=35)
                audit.save()
    
    def test_filter_by_date_range(self):
        """Test filtro por rango de fechas."""
        now = timezone.now()
        start_date = now - timedelta(days=7)
        
        result = services.get_audits_by_period(
            start_date=start_date,
            grouping='daily'
        )
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        # Debería incluir solo auditorías recientes
        total_in_range = sum(result['data'])
        self.assertGreaterEqual(total_in_range, 3)


class ReportAPITests(TestCase):
    """Tests para endpoints de API de reportería."""
    
    def setUp(self):
        """Configurar cliente API y usuario."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear datos de prueba
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            
            self.audit = Audit.objects.create(
                title='Test Audit',
                status=Audit.Status.PENDING
            )
    
    def test_audit_summary_endpoint(self):
        """Test endpoint de resumen de auditorías."""
        response = self.client.get('/api/reports/audits/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('by_status', response.data)
        self.assertIn('active', response.data)
        self.assertIn('deleted', response.data)
    
    def test_audit_by_period_endpoint(self):
        """Test endpoint de auditorías por período."""
        response = self.client.get('/api/reports/audits/by-period/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('labels', response.data)
        self.assertIn('data', response.data)
        self.assertIn('grouping', response.data)
    
    def test_audit_by_period_with_filters(self):
        """Test endpoint con filtros de fecha."""
        now = timezone.now()
        start = (now - timedelta(days=30)).isoformat()
        end = now.isoformat()
        
        response = self.client.get(
            f'/api/reports/audits/by-period/?start_date={start}&end_date={end}&grouping=weekly'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['grouping'], 'weekly')
    
    def test_audit_by_user_endpoint(self):
        """Test endpoint de productividad por usuario."""
        response = self.client.get('/api/reports/audits/by-user/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_events_by_audit_endpoint(self):
        """Test endpoint de eventos por auditoría."""
        response = self.client.get('/api/reports/events/by-audit/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_events', response.data)
        self.assertIn('upcoming_events', response.data)
        self.assertIn('by_audit', response.data)
    
    def test_evidence_summary_endpoint(self):
        """Test endpoint de resumen de evidencias."""
        response = self.client.get('/api/reports/evidences/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_evidences', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('by_audit', response.data)
    
    def test_unauthorized_access(self):
        """Test que endpoints requieren autenticación."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/reports/audits/summary/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReportPerformanceTests(TestCase):
    """Tests para validar performance de reportes."""
    
    def setUp(self):
        """Crear dataset de prueba más grande."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear 50 auditorías
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            
            for i in range(50):
                Audit.objects.create(
                    title=f'Audit {i}',
                    status=Audit.Status.PENDING if i % 2 == 0 else Audit.Status.COMPLETED
                )
    
    def test_audit_summary_performance(self):
        """Test que resumen de auditorías es rápido."""
        start = time()
        services.get_audit_summary()
        duration = time() - start
        
        # Debe completarse en menos de 1 segundo
        self.assertLess(duration, 1.0)
    
    def test_audit_by_period_performance(self):
        """Test que agrupación por período es rápida."""
        start = time()
        services.get_audits_by_period(grouping='monthly')
        duration = time() - start
        
        # Debe completarse en menos de 1 segundo
        self.assertLess(duration, 1.0)
    
    def test_audit_by_user_performance(self):
        """Test que productividad por usuario es rápida."""
        start = time()
        services.get_audits_by_user()
        duration = time() - start
        
        # Debe completarse en menos de 1 segundo
        self.assertLess(duration, 1.0)
