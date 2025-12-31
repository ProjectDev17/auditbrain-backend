from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from audits.models import Audit, AuditEvent
from core.middleware import _thread_locals
from datetime import datetime, timedelta


class AuditEventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        _thread_locals.user = self.user
        
        self.audit = Audit.objects.create(
            title='Test Audit',
            description='Test Description',
            status=Audit.Status.PENDING
        )
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_create_event(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        event_date = datetime.now() + timedelta(days=7)
        event = AuditEvent.objects.create(
            audit=self.audit,
            title='Revisión Inicial',
            description='Primera revisión de la auditoría',
            event_date=event_date
        )
        
        self.assertIsNotNone(event.id)
        self.assertEqual(event.title, 'Revisión Inicial')
        self.assertEqual(event.audit, self.audit)
        self.assertEqual(event.created_by, self.user.id)
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_event_soft_delete(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        event = AuditEvent.objects.create(
            audit=self.audit,
            title='Test Event',
            event_date=datetime.now()
        )
        
        event.delete()
        self.assertTrue(event.deleted)
    
    def test_event_ordering(self):
        event1 = AuditEvent.objects.create(
            audit=self.audit,
            title='Event 1',
            event_date=datetime.now() + timedelta(days=2)
        )
        event2 = AuditEvent.objects.create(
            audit=self.audit,
            title='Event 2',
            event_date=datetime.now() + timedelta(days=1)
        )
        
        events = AuditEvent.objects.filter(audit=self.audit, deleted=False)
        self.assertEqual(events[0], event2)  # Ordenado por event_date
        self.assertEqual(events[1], event1)
