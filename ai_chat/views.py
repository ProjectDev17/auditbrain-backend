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
                
            # Si hay tool calls, ejecutarlos y pedir respuesta final
            if tool_calls:
                # 1. Guardar mensaje del asistente con las llamadas a herramientas
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=assistant_message,
                    tool_calls=tool_calls
                )
                
                # 2. Ejecutar herramientas y preparar mensajes de resultados
                current_messages = ollama_service.format_messages_for_ollama(
                    conversation.messages.all()
                )
                
                for tool_call in tool_calls:
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function']['arguments']
                    
                    try:
                        result = execute_mcp_tool(tool_name, tool_args, request.user)
                        # Guardar resultado como mensaje de sistema o rol 'tool'
                        # Nota: Ollama usa el historial para entender el flujo
                        AIMessage.objects.create(
                            conversation=conversation,
                            role='system', # O 'tool' si el modelo lo soporta, usamos system para contexto
                            content=f"Resultado de {tool_name}: {json.dumps(result, ensure_ascii=False)}"
                        )
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        AIMessage.objects.create(
                            conversation=conversation,
                            role='system',
                            content=f"Error ejecutando {tool_name}: {str(e)}"
                        )
                
                # 3. Segunda llamada a Ollama para respuesta final en lenguaje natural
                final_messages = ollama_service.format_messages_for_ollama(
                    conversation.messages.all()
                )
                
                final_response = ollama_service.chat(
                    messages=final_messages,
                    stream=False
                )
                
                final_content = final_response.get('message', {}).get('content', '')
                
                # 4. Guardar respuesta final
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=final_content
                )
            else:
                # Si no hubo tool calls, guardar la respuesta única
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=assistant_message
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
    
    @action(detail=True, methods=['post'], url_path='chat-stream')
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
                # 1. Guardar mensaje del usuario
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                
                # 2. Primer paso: Llamar a Ollama (puede o no usar tools)
                messages = ollama_service.format_messages_for_ollama(
                    conversation.messages.all()
                )
                
                tools = None
                if enable_tools:
                    tools = get_audit_context_tools()
                
                full_response = ""
                all_tool_calls = []
                
                # Procesar primer stream
                for chunk_dict in ollama_service.chat(messages=messages, tools=tools, stream=True):
                    content = chunk_dict.get('content')
                    tool_calls = chunk_dict.get('tool_calls')
                    
                    if content:
                        full_response += content
                        # Enviar texto al usuario solo si no hay intención de tools detectada aún
                        # (O si el modelo decide enviar texto Y tools, aunque Ollama suele separar).
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    
                    if tool_calls:
                        all_tool_calls.extend(tool_calls)
                
                # 3. Si hubo tool calls, ejecutarlas y hacer un segundo paso
                if all_tool_calls:
                    # Guardar el mensaje del asistente con las tools
                    AIMessage.objects.create(
                        conversation=conversation,
                        role='assistant',
                        content=full_response,
                        tool_calls=all_tool_calls
                    )
                    
                    # Ejecutar cada herramienta
                    for tool_call in all_tool_calls:
                        tool_name = tool_call['function']['name']
                        tool_args = tool_call['function']['arguments']
                        
                        try:
                            result = execute_mcp_tool(tool_name, tool_args, request.user)
                            AIMessage.objects.create(
                                conversation=conversation,
                                role='system',
                                content=f"Resultado de {tool_name}: {json.dumps(result, ensure_ascii=False)}"
                            )
                        except Exception as e:
                            logger.error(f"Tool execution failed in stream: {e}")
                            AIMessage.objects.create(
                                conversation=conversation,
                                role='system',
                                content=f"Error ejecutando {tool_name}: {str(e)}"
                            )
                    
                    # Segundo paso: Stream de la interpretación en lenguaje natural
                    final_messages = ollama_service.format_messages_for_ollama(
                        conversation.messages.all()
                    )
                    
                    # Informar al frontend que estamos procesando (opcional, pero ayuda a la UX)
                    # yield f"data: {json.dumps({'status': 'interpreting'}, ensure_ascii=False)}\n\n"
                    
                    interpretation_response = ""
                    for chunk_dict in ollama_service.chat(messages=final_messages, stream=True):
                        content = chunk_dict.get('content')
                        if content:
                            interpretation_response += content
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    
                    # Guardar respuesta final interpretada
                    AIMessage.objects.create(
                        conversation=conversation,
                        role='assistant',
                        content=interpretation_response
                    )
                    
                else:
                    # Si no hubo tools, solo guardar la respuesta inicial completa
                    AIMessage.objects.create(
                        conversation=conversation,
                        role='assistant',
                        content=full_response
                    )
                
                # Actualizar timestamp de conversación
                conversation.save()
                
                # Enviar evento de finalización
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.exception(f"Streaming failed: {e}")
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        
        # Retornar respuesta streaming
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
