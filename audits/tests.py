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
        # Se mockea el get_current_user o se asume system/anonymous si no hay request
        # Para simular middleware, podemos usar un contexto o mockear get_current_user
        
        with patch('core.middleware.get_current_user', return_value=self.user):
            audit = Audit.objects.create(title="Test Audit", description="Testing")
            
            self.assertEqual(audit.title, "Test Audit")
            self.assertEqual(audit.status, Audit.Status.PENDING)
            self.assertEqual(audit.created_by, str(self.user.id))
            self.assertFalse(audit.deleted)
            
            # Verificar que se llamó al logger
            mock_logger.log_action.assert_called()
            args, kwargs = mock_logger.log_action.call_args
            self.assertEqual(kwargs['action'], 'CREATE')
            self.assertEqual(str(kwargs['user']), str(self.user.id))

    @patch('audits.signals.audit_logger')
    def test_soft_delete(self, mock_logger):
        """Prueba el soft delete."""
        with patch('core.middleware.get_current_user', return_value=self.user):
            audit = Audit.objects.create(title="To Delete")
            audit_id = audit.id
            
            # Delete
            audit.delete()
            
            # Refetch
            audit.refresh_from_db()
            self.assertTrue(audit.deleted)
            
            # Verificar log de eliminación
            # La primera llamada fue CREATE, la segunda debe ser DELETE
            self.assertEqual(mock_logger.log_action.call_count, 2)
            args, kwargs = mock_logger.log_action.call_args
            self.assertEqual(kwargs['action'], 'DELETE')
