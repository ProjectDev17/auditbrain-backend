from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from django.db import transaction
import json
import logging

from .models import AIConversation, AIMessage
from .serializers import (
    AIConversationSerializer,
    AIConversationListSerializer,
    AIMessageSerializer,
    ChatRequestSerializer
)
from .services import ollama_service
from .mcp_integration import get_audit_context_tools, execute_mcp_tool, format_tool_result_for_chat

logger = logging.getLogger(__name__)


class AIConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar conversaciones AI.
    
    Endpoints:
    - GET /api/ai-conversations/ - Listar conversaciones
    - POST /api/ai-conversations/ - Crear conversación
    - GET /api/ai-conversations/{id}/ - Detalle conversación
    - PATCH /api/ai-conversations/{id}/ - Actualizar título
    - DELETE /api/ai-conversations/{id}/ - Eliminar conversación
    - POST /api/ai-conversations/{id}/messages/ - Agregar mensaje
    - POST /api/ai-conversations/{id}/chat/ - Chat (respuesta completa)
    - POST /api/ai-conversations/{id}/chat-stream/ - Chat (streaming)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar conversaciones del usuario autenticado."""
        return AIConversation.objects.filter(
            user=self.request.user,
            deleted=False
        ).prefetch_related('messages')
    
    def get_serializer_class(self):
        """Usar serializer ligero para listados."""
        if self.action == 'list':
            return AIConversationListSerializer
        return AIConversationSerializer
    
    def perform_create(self, serializer):
        """Asignar usuario al crear conversación."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """
        Agregar mensaje a la conversación.
        
        POST /api/ai-conversations/{id}/messages/
        Body: {"role": "user|assistant", "content": "..."}
        """
        conversation = self.get_object()
        
        # Validar datos
        message_serializer = AIMessageSerializer(data=request.data)
        message_serializer.is_valid(raise_exception=True)
        
        # Crear mensaje
        message = AIMessage.objects.create(
            conversation=conversation,
            **message_serializer.validated_data
        )
        
        # Actualizar timestamp de conversación
        conversation.save()
        
        # Retornar conversación completa
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        Enviar mensaje y obtener respuesta de Ollama (respuesta completa).
        
        POST /api/ai-conversations/{id}/chat/
        Body: {
            "message": "¿Cuántas auditorías tengo?",
            "enable_tools": true
        }
        """
        conversation = self.get_object()
        
        # Validar request
        chat_serializer = ChatRequestSerializer(data=request.data)
        chat_serializer.is_valid(raise_exception=True)
        
        user_message = chat_serializer.validated_data['message']
        enable_tools = chat_serializer.validated_data.get('enable_tools', True)
        
        try:
            with transaction.atomic():
                # Guardar mensaje del usuario
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                
                # Preparar mensajes para Ollama
                messages = ollama_service.format_messages_for_ollama(
                    conversation.messages.all()
                )
                
                # Obtener tools si está habilitado
                tools = None
                if enable_tools:
                    tools = get_audit_context_tools()
                
                # Llamar a Ollama
                response = ollama_service.chat(
                    messages=messages,
                    tools=tools,
                    stream=False
                )
                
                # Extraer respuesta
                assistant_message = response.get('message', {}).get('content', '')
                tool_calls = response.get('message', {}).get('tool_calls')
                
                # Si hay tool calls, ejecutarlos
                if tool_calls:
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call['function']['name']
                        tool_args = tool_call['function']['arguments']
                        
                        try:
                            result = execute_mcp_tool(tool_name, tool_args, request.user)
                            formatted_result = format_tool_result_for_chat(tool_name, result)
                            tool_results.append(formatted_result)
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")
                            tool_results.append(f"Error ejecutando {tool_name}: {str(e)}")
                    
                    # Agregar resultados al mensaje
                    if tool_results:
                        assistant_message += "\n\n" + "\n\n".join(tool_results)
                
                # Guardar respuesta del asistente
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=assistant_message,
                    tool_calls=tool_calls
                )
                
                # Actualizar conversación
                conversation.save()
            
            # Retornar conversación actualizada
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Chat failed: {e}")
            return Response(
                {"error": f"Error en el chat: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def chat_stream(self, request, pk=None):
        """
        Enviar mensaje y obtener respuesta de Ollama en streaming (SSE).
        
        POST /api/ai-conversations/{id}/chat-stream/
        Body: {
            "message": "¿Cuántas auditorías tengo?",
            "enable_tools": true
        }
        """
        conversation = self.get_object()
        
        # Validar request
        chat_serializer = ChatRequestSerializer(data=request.data)
        chat_serializer.is_valid(raise_exception=True)
        
        user_message = chat_serializer.validated_data['message']
        enable_tools = chat_serializer.validated_data.get('enable_tools', True)
        
        def event_stream():
            """Generador para Server-Sent Events."""
            try:
                # Guardar mensaje del usuario
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                
                # Preparar mensajes
                messages = ollama_service.format_messages_for_ollama(
                    conversation.messages.all()
                )
                
                # Obtener tools si está habilitado
                tools = None
                if enable_tools:
                    tools = get_audit_context_tools()
                
                # Stream de Ollama
                full_response = ""
                for chunk in ollama_service.chat(messages=messages, tools=tools, stream=True):
                    full_response += chunk
                    # Enviar chunk como SSE
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # Guardar respuesta completa
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=full_response
                )
                
                # Actualizar conversación
                conversation.save()
                
                # Enviar evento de finalización
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.exception(f"Streaming failed: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        # Retornar respuesta streaming
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
