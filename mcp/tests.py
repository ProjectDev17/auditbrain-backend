"""
Tests for MCP Module.

Run with: python manage.py test mcp.tests
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from mcp.tools import ToolRegistry
from mcp.security import ScopeValidator, validate_scope, get_user_scopes
from mcp.ontologies import OntologyManager, get_ontology_manager


class OntologyManagerTests(TestCase):
    """Tests for OntologyManager class."""
    
    def setUp(self):
        self.manager = OntologyManager()
    
    def test_register_tool(self):
        """Test tool registration."""
        self.manager.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            scope="AuditRead"
        )
        
        tool = self.manager.get_tool("test_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool["name"], "test_tool")
        self.assertEqual(tool["requiredScope"], "AuditRead")
    
    def test_list_tools(self):
        """Test listing tools."""
        self.manager.register_tool(
            name="tool1",
            description="Tool 1",
            input_schema={},
            output_schema={},
            scope="AuditRead"
        )
        self.manager.register_tool(
            name="tool2",
            description="Tool 2",
            input_schema={},
            output_schema={},
            scope="AuditWrite"
        )
        
        tools = self.manager.list_tools()
        self.assertEqual(len(tools), 2)
    
    def test_check_role_has_scope_fallback(self):
        """Test scope checking with fallback (no rdflib)."""
        # Admin should have all scopes
        self.assertTrue(self.manager.check_role_has_scope("Admin", "AuditRead"))
        self.assertTrue(self.manager.check_role_has_scope("Admin", "UserManage"))
        
        # Auditor should have limited scopes
        self.assertTrue(self.manager.check_role_has_scope("Auditor", "AuditRead"))
        self.assertFalse(self.manager.check_role_has_scope("Auditor", "UserManage"))


class ToolRegistryTests(TestCase):
    """Tests for ToolRegistry class."""
    
    def setUp(self):
        ToolRegistry.clear()
    
    def test_register_decorator(self):
        """Test registering a tool with decorator."""
        @ToolRegistry.register(
            name="test_decorated_tool",
            description="Test tool",
            input_schema={"type": "object"},
            scope="AuditRead"
        )
        def test_handler(params, context):
            return {"result": "success"}
        
        tool = ToolRegistry.get_tool("test_decorated_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "test_decorated_tool")
    
    def test_execute_tool(self):
        """Test executing a registered tool."""
        @ToolRegistry.register(
            name="echo_tool",
            description="Echo tool",
            input_schema={"type": "object"},
            scope="AuditRead"
        )
        def echo_handler(params, context):
            return {"echo": params.get("message")}
        
        result = ToolRegistry.execute(
            "echo_tool",
            {"message": "hello"},
            {"user": None}
        )
        
        self.assertEqual(result["echo"], "hello")
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        with self.assertRaises(ValueError):
            ToolRegistry.execute("nonexistent", {}, {})
    
    def test_list_tools_mcp_format(self):
        """Test listing tools in MCP format."""
        @ToolRegistry.register(
            name="format_test",
            description="Format test",
            input_schema={"type": "object", "properties": {"foo": {"type": "string"}}},
            scope="AuditRead"
        )
        def handler(params, context):
            return {}
        
        tools = ToolRegistry.list_tools()
        self.assertEqual(len(tools), 1)
        self.assertIn("name", tools[0])
        self.assertIn("description", tools[0])
        self.assertIn("inputSchema", tools[0])


class ScopeValidatorTests(TestCase):
    """Tests for ScopeValidator class."""
    
    def test_get_user_role_superuser(self):
        """Test role detection for superuser."""
        User = get_user_model()
        user = User(is_superuser=True, is_staff=True)
        
        validator = ScopeValidator()
        role = validator.get_user_role(user)
        
        self.assertEqual(role, "Admin")
    
    def test_get_user_role_staff(self):
        """Test role detection for staff user."""
        User = get_user_model()
        user = User(is_superuser=False, is_staff=True)
        
        validator = ScopeValidator()
        role = validator.get_user_role(user)
        
        self.assertEqual(role, "Auditor")
    
    def test_get_user_role_anonymous(self):
        """Test role detection for anonymous user."""
        validator = ScopeValidator()
        role = validator.get_user_role(None)
        
        self.assertEqual(role, "Anonymous")
    
    def test_get_user_scopes(self):
        """Test getting scopes for a user."""
        User = get_user_model()
        admin = User(is_superuser=True)
        
        scopes = get_user_scopes(admin)
        
        self.assertIn("AuditRead", scopes)
        self.assertIn("UserManage", scopes)


class MCPServerTests(TestCase):
    """Tests for MCP Server endpoints."""
    
    def setUp(self):
        self.client = Client()
        # Clear tools and register test tools
        ToolRegistry.clear()
        
        @ToolRegistry.register(
            name="test_server_tool",
            description="Test tool for server",
            input_schema={"type": "object"},
            scope="AuditRead"
        )
        def test_handler(params, context):
            return {"status": "ok"}
    
    def test_initialize(self):
        """Test MCP initialize request."""
        response = self.client.post(
            '/mcp/',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertIn("result", data)
        self.assertIn("protocolVersion", data["result"])
        self.assertIn("serverInfo", data["result"])
    
    def test_list_tools(self):
        """Test tools/list request."""
        response = self.client.post(
            '/mcp/',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        self.assertIn("tools", data["result"])
    
    def test_call_tool_without_auth(self):
        """Test tools/call without authentication."""
        response = self.client.post(
            '/mcp/',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "test_server_tool",
                    "arguments": {}
                }
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
    
    def test_unknown_method(self):
        """Test calling unknown method."""
        response = self.client.post(
            '/mcp/',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 4,
                "method": "unknown/method",
                "params": {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
    
    def test_invalid_json(self):
        """Test sending invalid JSON."""
        response = self.client.post(
            '/mcp/',
            data='not valid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_discovery_endpoint(self):
        """Test discovery GET endpoint."""
        response = self.client.get('/mcp/discover/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("serverInfo", data)
        self.assertIn("tools", data)
