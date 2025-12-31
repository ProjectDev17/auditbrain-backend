from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.verify_url = '/api/auth/token/verify/'
        
        self.user_data = {
            'email': 'test@auditbrain.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration(self):
        """Test registro de nuevo usuario."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])
        
        # Verificar que el usuario fue creado
        user_exists = User.objects.filter(email=self.user_data['email']).exists()
        self.assertTrue(user_exists)
    
    def test_registration_password_mismatch(self):
        """Test que las contraseñas deben coincidir."""
        data = self.user_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test login con credenciales correctas."""
        # Crear usuario
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        
        # Intentar login
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login con credenciales incorrectas."""
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@test.com',
            'password': 'wrongpass'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test refresh de token JWT."""
        # Crear usuario y hacer login
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        login_response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        
        refresh_token = login_response.data['refresh']
        
        # Refrescar token
        response = self.client.post(self.refresh_url, {
            'refresh': refresh_token
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_verify(self):
        """Test verificación de token JWT."""
        # Crear usuario y hacer login
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        login_response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        
        access_token = login_response.data['access']
        
        # Verificar token
        response = self.client.post(self.verify_url, {
            'token': access_token
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
