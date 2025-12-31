from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from authentication.services import PasswordResetService

User = get_user_model()


class PasswordResetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reset_request_url = '/api/auth/password/reset/'
        self.reset_confirm_url = '/api/auth/password/reset/confirm/'
        
        self.user = User.objects.create_user(
            email='test@auditbrain.com',
            password='OldPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_password_reset_request(self):
        """Test solicitud de reset de contraseña."""
        response = self.client.post(self.reset_request_url, {
            'email': self.user.email
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_password_reset_nonexistent_email(self):
        """Test reset con email inexistente (debe retornar mismo mensaje)."""
        response = self.client.post(self.reset_request_url, {
            'email': 'nonexistent@test.com'
        }, format='json')
        
        # Por seguridad, debe retornar el mismo mensaje
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_password_reset_confirm_valid_token(self):
        """Test confirmación de reset con token válido."""
        # Generar token
        token = PasswordResetService.generate_token(self.user.email)
        
        # Confirmar reset
        response = self.client.post(self.reset_confirm_url, {
            'token': token,
            'new_password': 'NewPass123!'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
    
    def test_password_reset_confirm_invalid_token(self):
        """Test confirmación con token inválido."""
        response = self.client.post(self.reset_confirm_url, {
            'token': 'invalid_token',
            'new_password': 'NewPass123!'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_token_generation_and_verification(self):
        """Test generación y verificación de tokens."""
        email = 'test@auditbrain.com'
        
        # Generar token
        token = PasswordResetService.generate_token(email)
        self.assertIsNotNone(token)
        
        # Verificar token
        verified_email = PasswordResetService.verify_token(token)
        self.assertEqual(verified_email, email)
    
    def test_invalid_token_verification(self):
        """Test verificación de token inválido."""
        verified_email = PasswordResetService.verify_token('invalid_token')
        self.assertIsNone(verified_email)
