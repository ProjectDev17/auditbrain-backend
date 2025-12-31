from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from audits.models import Audit, Evidence
from core.middleware import _thread_locals


class EvidenceModelTest(TestCase):
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
    def test_create_evidence(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        # Crear archivo de prueba
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        evidence = Evidence.objects.create(
            audit=self.audit,
            file=test_file
        )
        
        self.assertIsNotNone(evidence.id)
        self.assertEqual(evidence.audit, self.audit)
        self.assertEqual(evidence.file_type, 'pdf')
        self.assertEqual(evidence.created_by, self.user.id)
    
    @patch('audits.signals.get_current_user')
    @patch('core.models.get_current_user')
    def test_evidence_soft_delete(self, mock_core_user, mock_signals_user):
        mock_core_user.return_value = self.user.id
        mock_signals_user.return_value = self.user.id
        
        test_file = SimpleUploadedFile("test.pdf", b"content")
        evidence = Evidence.objects.create(
            audit=self.audit,
            file=test_file
        )
        
        evidence.delete()
        self.assertTrue(evidence.deleted)
    
    def test_file_type_extraction(self):
        test_file = SimpleUploadedFile("document.docx", b"content")
        evidence = Evidence.objects.create(
            audit=self.audit,
            file=test_file
        )
        
        self.assertEqual(evidence.file_type, 'docx')
