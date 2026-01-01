from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, 
    UserSerializer,
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer,
    UserManagementSerializer
)
from .services import PasswordResetService

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD completo de usuarios backoffice.
    Solo accesible por administradores.
    Implementa Soft Delete.
    """
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated] # Ajustar a IsAdminUser si se requiere estricto

    def perform_destroy(self, instance):
        # Soft Delete: Desactivar usuario en lugar de borrar
        instance.is_active = False
        instance.save()


class RegisterView(generics.CreateAPIView):
    """
    Endpoint para registro de nuevos usuarios.
    No requiere autenticación.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Usuario registrado exitosamente.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Endpoint para solicitar recuperación de contraseña.
    No requiere autenticación.
    """
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        PasswordResetService.send_reset_email(email)
        
        # Siempre retornar el mismo mensaje por seguridad
        return Response({
            'message': 'Si el email existe, recibirás instrucciones de recuperación.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Endpoint para confirmar nueva contraseña con token.
    No requiere autenticación.
    """
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        success = PasswordResetService.reset_password(token, new_password)
        
        if success:
            return Response({
                'message': 'Contraseña actualizada exitosamente.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Token inválido o expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    Endpoint para obtener perfil del usuario autenticado.
    Requiere autenticación.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
