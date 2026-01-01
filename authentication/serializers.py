from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para información básica del usuario."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


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
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_auditor', 'password']
        read_only_fields = ['id']
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
