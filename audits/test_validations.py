from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from audits.models import Audit
from audits.serializers import AuditSerializer
from core.middleware import _thread_locals
from rest_framework.exceptions import ValidationError


class AuditValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        _thread_locals.user = self.user
    
    def test_title_min_length_validation(self):
        """Test que el título debe tener al menos 5 caracteres."""
        serializer = AuditSerializer(data={
            'title': 'ABC',  # Solo 3 caracteres
            'status': 'pending'
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_cannot_modify_deleted_audit(self, mock_core_user, mock_signals_user):
        """Test que no se puede modificar una auditoría eliminada."""
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        audit = Audit.objects.create(
            title='Test Audit',
            status=Audit.Status.PENDING
        )
        audit.delete()  # Soft delete
        
        serializer = AuditSerializer(audit, data={
            'title': 'Updated Title'
        }, partial=True)
        
        self.assertFalse(serializer.is_valid())
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_cannot_change_completed_to_pending(self, mock_core_user, mock_signals_user):
        """Test que no se puede cambiar de completed a pending."""
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        audit = Audit.objects.create(
            title='Test Audit',
            status=Audit.Status.COMPLETED
        )
        
        serializer = AuditSerializer(audit, data={
            'status': 'pending'
        }, partial=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)


class AuditFilterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        _thread_locals.user = self.user
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_filter_by_status(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        Audit.objects.create(title='Audit 1', status=Audit.Status.PENDING)
        Audit.objects.create(title='Audit 2', status=Audit.Status.IN_PROGRESS)
        Audit.objects.create(title='Audit 3', status=Audit.Status.PENDING)
        
        pending_audits = Audit.objects.filter(status=Audit.Status.PENDING, deleted=False)
        self.assertEqual(pending_audits.count(), 2)
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_exclude_deleted(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        audit1 = Audit.objects.create(title='Audit 1', status=Audit.Status.PENDING)
        audit2 = Audit.objects.create(title='Audit 2', status=Audit.Status.PENDING)
        audit2.delete()
        
        active_audits = Audit.objects.filter(deleted=False)
        self.assertEqual(active_audits.count(), 1)
        self.assertEqual(active_audits.first(), audit1)
