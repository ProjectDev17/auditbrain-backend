from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from .models import Audit
from core.models import AuditableModel

class AuditModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    @patch('audits.signals.audit_logger')
    def test_create_audit(self, mock_logger):
        """Prueba la creación de una auditoría y la llamada al logger."""
        
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
