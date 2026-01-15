from rest_framework import serializers
from .models import AIConversation, AIMessage


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes AI."""
    
    class Meta:
        model = AIMessage
        fields = ['id', 'role', 'content', 'timestamp', 'tool_calls']
        read_only_fields = ['id', 'timestamp']


class AIConversationListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de conversaciones."""
    
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'message_count', 'last_message'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'timestamp': last_msg.timestamp
            }
        return None


class AIConversationSerializer(serializers.ModelSerializer):
    """Serializer completo para conversaciones con mensajes."""
    
    messages = AIMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'messages', 'message_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def create(self, validated_data):
        # Asignar usuario del request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChatRequestSerializer(serializers.Serializer):
    """Serializer para peticiones de chat."""
    
    message = serializers.CharField(required=True)
    stream = serializers.BooleanField(default=False)
    enable_tools = serializers.BooleanField(default=True)
