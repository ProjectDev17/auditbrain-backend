"""
MCP Tool Registry with decorator-based registration.

Provides a registry for MCP tools that can be discovered and executed
by any MCP-compatible client.
"""
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
import logging
import json

from .ontologies import get_ontology_manager

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool with metadata and handler."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_scope: str
    handler: Callable
    annotations: Dict[str, Any] = field(default_factory=dict)
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": self.annotations
        }


class ToolRegistry:
    """
    Central registry for MCP tools.
    
    Tools are registered using the @register decorator and can be
    listed and executed through the registry methods.
    """
    _tools: Dict[str, MCPTool] = {}
    _initialized: bool = False
    
    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Optional[Dict[str, Any]] = None,
        scope: str = "AuditRead",
        annotations: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            name: Unique tool identifier
            description: Human-readable description
            input_schema: JSON Schema for input parameters
            output_schema: JSON Schema for output (optional)
            scope: Required permission scope
            annotations: Additional metadata
        
        Example:
            @ToolRegistry.register(
                name="list_audits",
                description="List all audits",
                input_schema={"type": "object", "properties": {...}},
                scope="AuditRead"
            )
            def list_audits(params, context):
                return [...]
        """
        def decorator(func: Callable) -> Callable:
            tool = MCPTool(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema or {"type": "object"},
                required_scope=scope,
                handler=func,
                annotations=annotations or {}
            )
            cls._tools[name] = tool
            
            # Register in ontology
            try:
                ontology = get_ontology_manager()
                ontology.register_tool(
                    name=name,
                    description=description,
                    input_schema=input_schema,
                    output_schema=output_schema or {},
                    scope=scope
                )
            except Exception as e:
                logger.warning(f"Failed to register tool {name} in ontology: {e}")
            
            logger.info(f"Registered MCP tool: {name}")
            return func
        return decorator
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> list:
        """List all registered tools in MCP format."""
        return [tool.to_mcp_format() for tool in cls._tools.values()]
    
    @classmethod
    def list_tools_for_scope(cls, user_scopes: list) -> list:
        """List tools that the user has permission to access."""
        return [
            tool.to_mcp_format()
            for tool in cls._tools.values()
            if tool.required_scope in user_scopes
        ]
    
    @classmethod
    def execute(cls, name: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            params: Tool parameters
            context: Execution context (user, request, etc.)
        
        Returns:
            Tool execution result
        
        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        tool = cls.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        
        logger.info(f"Executing tool: {name} with params: {json.dumps(params, default=str)}")
        
        try:
            result = tool.handler(params, context)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            raise
    
    @classmethod
    def get_required_scope(cls, name: str) -> Optional[str]:
        """Get the required scope for a tool."""
        tool = cls.get_tool(name)
        return tool.required_scope if tool else None
    
    @classmethod
    def clear(cls):
        """Clear all registered tools (useful for testing)."""
        cls._tools.clear()
