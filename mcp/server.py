"""
MCP Server - JSON-RPC handler for Model Context Protocol.

Implements the MCP specification for tool discovery and execution.
Reference: https://modelcontextprotocol.io/specification
"""
import json
import logging
from typing import Dict, Any, Optional

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .tools import ToolRegistry
from .security import validate_scope, get_user_scopes

logger = logging.getLogger(__name__)

# MCP Protocol Version
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "antigravity-mcp"
SERVER_VERSION = "1.0.0"


class MCPError(Exception):
    """Base exception for MCP errors."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


# Standard JSON-RPC error codes
class ErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@method_decorator(csrf_exempt, name='dispatch')
class MCPServerView(View):
    """
    MCP Server endpoint implementing JSON-RPC 2.0.
    
    Supports:
    - initialize: Protocol handshake
    - tools/list: List available tools
    - tools/call: Execute a tool
    - resources/list: List available resources
    - resources/read: Read a resource
    """
    
    def post(self, request):
        """Handle MCP JSON-RPC requests."""
        msg_id = None
        
        try:
            # Parse request body
            try:
                message = json.loads(request.body)
            except json.JSONDecodeError as e:
                raise MCPError(ErrorCodes.PARSE_ERROR, f"Invalid JSON: {e}")
            
            msg_id = message.get("id")
            method = message.get("method")
            params = message.get("params", {})
            
            if not method:
                raise MCPError(ErrorCodes.INVALID_REQUEST, "Missing 'method' field")
            
            # Authenticate user (optional for some methods)
            user = self._authenticate(request)
            
            # Handle method
            result = self._handle_method(method, params, request, user)
            
            return JsonResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            })
            
        except MCPError as e:
            return JsonResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "data": e.data
                }
            }, status=400)
            
        except PermissionError as e:
            return JsonResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32001,
                    "message": str(e)
                }
            }, status=403)
            
        except Exception as e:
            logger.exception(f"MCP Server error: {e}")
            return JsonResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": ErrorCodes.INTERNAL_ERROR,
                    "message": str(e)
                }
            }, status=500)
    
    def _authenticate(self, request) -> Optional[Any]:
        """Authenticate request using JWT."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(
                jwt_auth.get_raw_token(auth_header.encode())
            )
            user = jwt_auth.get_user(validated_token)
            return user
        except AuthenticationFailed:
            return None
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return None
    
    def _handle_method(self, method: str, params: Dict, request, user) -> Dict:
        """Route method to appropriate handler."""
        handlers = {
            "initialize": self._handle_initialize,
            "notifications/initialized": self._handle_initialized,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
        }
        
        handler = handlers.get(method)
        if handler is None:
            raise MCPError(ErrorCodes.METHOD_NOT_FOUND, f"Unknown method: {method}")
        
        return handler(params, request, user)
    
    def _handle_initialize(self, params: Dict, request, user) -> Dict:
        """Handle initialize request - protocol handshake."""
        client_info = params.get("clientInfo", {})
        logger.info(f"MCP Initialize from client: {client_info.get('name', 'unknown')}")
        
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            },
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                }
            }
        }
    
    def _handle_initialized(self, params: Dict, request, user) -> Dict:
        """Handle initialized notification."""
        logger.info("MCP session initialized")
        return {}
    
    def _handle_list_tools(self, params: Dict, request, user) -> Dict:
        """Handle tools/list request."""
        if user:
            user_scopes = get_user_scopes(user)
            tools = ToolRegistry.list_tools_for_scope(user_scopes)
        else:
            # Return all tools for discovery, but execution requires auth
            tools = ToolRegistry.list_tools()
        
        return {"tools": tools}
    
    def _handle_call_tool(self, params: Dict, request, user) -> Dict:
        """Handle tools/call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise MCPError(ErrorCodes.INVALID_PARAMS, "Missing 'name' parameter")
        
        # Get tool
        tool = ToolRegistry.get_tool(name)
        if tool is None:
            raise MCPError(ErrorCodes.INVALID_PARAMS, f"Tool '{name}' not found")
        
        # Validate authentication
        if not user:
            raise PermissionError("Authentication required to execute tools")
        
        # Validate scope
        if not validate_scope(user, tool.required_scope):
            raise PermissionError(
                f"Insufficient permissions. Required scope: {tool.required_scope}"
            )
        
        # Execute tool
        context = {
            "user": user,
            "request": request,
        }
        
        try:
            result = ToolRegistry.execute(name, arguments, context)
            
            # Format result as MCP content
            if isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, dict) or isinstance(result, list):
                content = [{"type": "text", "text": json.dumps(result, default=str)}]
            else:
                content = [{"type": "text", "text": str(result)}]
            
            return {"content": content}
            
        except Exception as e:
            logger.exception(f"Tool execution failed: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    def _handle_list_resources(self, params: Dict, request, user) -> Dict:
        """Handle resources/list request."""
        # Resources can be extended later
        resources = []
        return {"resources": resources}
    
    def _handle_read_resource(self, params: Dict, request, user) -> Dict:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not uri:
            raise MCPError(ErrorCodes.INVALID_PARAMS, "Missing 'uri' parameter")
        
        # Resource reading can be extended later
        raise MCPError(ErrorCodes.INVALID_PARAMS, f"Resource not found: {uri}")


@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryView(View):
    """Simple discovery endpoint for non-MCP clients."""
    
    def get(self, request):
        """Return server capabilities and tools."""
        return JsonResponse({
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            },
            "tools": ToolRegistry.list_tools()
        })
