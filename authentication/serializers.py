from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group, Permission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para información básica del usuario."""
    is_auditor = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_active', 'is_auditor', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_is_auditor(self, obj):
        return obj.groups.filter(name='Auditors').exists()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Serializer para incluir información adicional del usuario en la respuesta."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Añadir información del usuario a la respuesta
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_auditor': self.user.groups.filter(name='Auditors').exists(),
            'is_active': self.user.is_active,
            'created_at': self.user.date_joined,
            'updated_at': self.user.updated_at,
            'created_by': str(self.user.created_by.id) if self.user.created_by else None,
            'updated_by': str(self.user.updated_by.id) if self.user.updated_by else None,
        }
        
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos usuarios."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Generar username desde email si no existe
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email'].split('@')[0]
        user = User.objects.create_user(**validated_data)
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar recuperación de contraseña."""
    
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar nueva contraseña."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class UserManagementSerializer(serializers.ModelSerializer):
    """
    Serializer para gestión administrativa de usuarios (CRUD completo).
    Incluye lógica para asignar/remover grupo de Auditores.
    """
    is_auditor = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_auditor', 'password', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
        extra_kwargs = {
            'email': {'required': True} 
        }

    def get_is_auditor(self, obj):
        return obj.groups.filter(name='Auditors').exists()

    def create(self, validated_data):
        is_auditor = self.context['request'].data.get('is_auditor', False)
        password = validated_data.pop('password', None)
        
        # Generar username
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email'].split('@')[0]
            
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save()

        if is_auditor:
            from django.contrib.auth.models import Group
            group, _ = Group.objects.get_or_create(name='Auditors')
            user.groups.add(group)
            
        return user

    def update(self, instance, validated_data):
        is_auditor = self.context['request'].data.get('is_auditor')
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        
        if is_auditor is not None:
            from django.contrib.auth.models import Group
            group, _ = Group.objects.get_or_create(name='Auditors')
            if is_auditor:
                instance.groups.add(group)
            else:
                instance.groups.remove(group)
                
        return instance


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos de Django."""
    
    class Meta:
        from django.contrib.auth.models import Permission
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de usuario."""
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Permission.objects.all(),
        required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']
