"""
Integración con MCP Tools para proporcionar contexto de auditorías al chat AI.
"""
import logging
from typing import List, Dict, Any
from mcp.tools import ToolRegistry

logger = logging.getLogger(__name__)


def get_audit_context_tools() -> List[Dict[str, Any]]:
    """
    Obtiene las tools MCP formateadas para Ollama.
    
    Returns:
        Lista de tools en formato compatible con Ollama
    """
    # Obtener tools registradas en MCP
    mcp_tools = ToolRegistry.list_tools()
    
    # Convertir al formato de Ollama
    ollama_tools = []
    
    for tool in mcp_tools:
        ollama_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("inputSchema", {})
            }
        }
        ollama_tools.append(ollama_tool)
    
    return ollama_tools


def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any], user) -> Any:
    """
    Ejecuta una tool MCP y retorna el resultado.
    
    Args:
        tool_name: Nombre de la tool a ejecutar
        arguments: Argumentos para la tool
        user: Usuario que ejecuta la tool
    
    Returns:
        Resultado de la ejecución de la tool
    
    Raises:
        Exception: Si la tool no existe o falla la ejecución
    """
    try:
        # Validar que la tool existe
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Preparar contexto
        context = {
            "user": user,
            "request": None  # No hay request en contexto de chat
        }
        
        # Ejecutar tool
        result = ToolRegistry.execute(tool_name, arguments, context)
        
        logger.info(f"Tool '{tool_name}' executed successfully by user {user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
        raise Exception(f"Error ejecutando {tool_name}: {str(e)}")


def format_tool_result_for_chat(tool_name: str, result: Any) -> str:
    """
    Formatea el resultado de una tool para incluirlo en el chat.
    
    Args:
        tool_name: Nombre de la tool ejecutada
        result: Resultado de la tool
    
    Returns:
        Texto formateado para el chat
    """
    import json
    
    if isinstance(result, (dict, list)):
        # Formatear JSON de forma legible
        formatted = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        return f"Resultado de {tool_name}:\n```json\n{formatted}\n```"
    else:
        return f"Resultado de {tool_name}: {str(result)}"
