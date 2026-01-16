"""
Servicio para integración con Ollama AI.
Maneja comunicación con el servidor Ollama local para chat y streaming.
"""
import json
import logging
import requests
from typing import List, Dict, Any, Generator, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Cliente para interactuar con Ollama API."""
    
    def __init__(self):
        self.config = settings.OLLAMA_CONFIG
        self.base_url = self.config['BASE_URL']
        self.model = self.config['MODEL']
        self.temperature = self.config['TEMPERATURE']
        self.max_tokens = self.config['MAX_TOKENS']
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Envía mensajes a Ollama y obtiene respuesta.
        
        Args:
            messages: Lista de mensajes en formato [{"role": "user", "content": "..."}]
            tools: Lista opcional de tools disponibles
            stream: Si True, retorna generador para streaming
        
        Returns:
            Respuesta de Ollama o generador si stream=True
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            if stream:
                return self._chat_stream(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise Exception(f"Error al comunicarse con Ollama: {str(e)}")
    
    def _chat_stream(self, url: str, payload: Dict) -> Generator[str, None, None]:
        """
        Genera respuesta en streaming.
        
        Yields:
            Chunks de texto de la respuesta
        """
        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            
                            # Ollama envía el contenido en chunk['message']['content']
                            message = chunk.get('message', {})
                            content = message.get('content')
                            tool_calls = message.get('tool_calls')
                            
                            if content or tool_calls:
                                yield {
                                    'content': content,
                                    'tool_calls': tool_calls
                                }
                            
                            # Si el chunk indica que terminó
                            if chunk.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse chunk: {line}")
                            continue
                            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise Exception(f"Error en streaming de Ollama: {str(e)}")
    
    def format_messages_for_ollama(
        self,
        conversation_messages: List,
        include_system: bool = True,
        user = None
    ) -> List[Dict[str, str]]:
        """
        Formatea mensajes de la BD al formato de Ollama.
        
        Args:
            conversation_messages: QuerySet o lista de AIMessage
            include_system: Si incluir mensaje de sistema
        
        Returns:
            Lista de mensajes formateados
        """
        messages = []
        
        # Agregar system prompt si está habilitado
        if include_system and self.config.get('SYSTEM_PROMPT'):
            from datetime import datetime
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            user_info = ""
            if user:
                user_info = f"\n\nUSUARIO ACTUAL:\n- Nombre: {user.first_name} {user.last_name}\n- Email: {user.email}\n- ID: {user.id}"
            
            system_prompt = f"{self.config['SYSTEM_PROMPT']}\n\nFecha actual del sistema: {current_date}{user_info}"
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Agregar mensajes de la conversación
        for msg in conversation_messages:
            # Asegurar que el rol sea uno de los soportados por Ollama 
            # (user, assistant, system, tool).
            role = msg.role
            
            message_dict = {
                "role": role,
                "content": msg.content
            }
            
            # CRITICAL: Si el mensaje del asistente tiene tool_calls, 
            # DEBEN incluirse para mantener el contexto.
            if role == 'assistant' and msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            messages.append(message_dict)
        
        return messages


# Instancia singleton
ollama_service = OllamaService()
