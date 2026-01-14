from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import Audit, AuditType
from core.models import AuditableModel
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AuditModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', username='testuser', password='password')

    @patch('audits.signals.audit_logger')
    def test_create_audit(self, mock_logger):
        """Prueba la creación de una auditoría y la llamada al logger."""
        
        # Patch en ambos lugares donde se importa get_current_user
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            audit = Audit.objects.create(title="Test Audit", description="Testing")
            
            self.assertEqual(audit.title, "Test Audit")
            self.assertEqual(audit.status, Audit.Status.PENDING)
            self.assertEqual(audit.created_by, str(self.user.id))
            self.assertFalse(audit.deleted)
            
            # Verificar que se llamó al logger
            mock_logger.log_action.assert_called()
            args, kwargs = mock_logger.log_action.call_args
            self.assertEqual(kwargs['action'], 'CREATE')
            # El logger recibe el user object
            self.assertEqual(kwargs['user'], self.user)

    @patch('audits.signals.audit_logger')
    def test_soft_delete(self, mock_logger):
        """Prueba el soft delete."""
        with patch('core.models.get_current_user', return_value=self.user), \
             patch('audits.signals.get_current_user', return_value=self.user):
            audit = Audit.objects.create(title="To Delete")
            mock_logger.reset_mock() # Limpiar llamada de creación
            
            # Delete
            audit.delete()
            
            # Refetch
            audit.refresh_from_db()
            self.assertTrue(audit.deleted)
            
            # Verificar log de eliminación
            mock_logger.log_action.assert_called_once()
            args, kwargs = mock_logger.log_action.call_args
            self.assertEqual(kwargs['action'], 'DELETE')


class AuditViewSetMissingAuditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user and authenticate
        self.user = User.objects.create_user(email='api@test.com', username='apiuser', password='password')
        self.client.force_authenticate(user=self.user)
        # Create an audit type
        self.audit_type = AuditType.objects.create(name='Type1')
        # Create an audit (though we won't use it for the missing test ideally)
        self.audit = Audit.objects.create(title='Test Audit', audit_type=self.audit_type, created_by=self.user)
        # Non-existent ID
        self.nonexistent_audit_id = '00000000-0000-0000-0000-000000000000'

    def test_get_events_invalid_audit(self):
        url = reverse('audit-events-list', kwargs={'audit_pk': self.nonexistent_audit_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_evidences_invalid_audit(self):
        url = reverse('audit-evidences-list', kwargs={'audit_pk': self.nonexistent_audit_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
