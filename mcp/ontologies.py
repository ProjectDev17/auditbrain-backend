"""
RDF Ontologies for MCP Tools, Capabilities and Permissions.

Uses rdflib to define semantic models that describe available tools,
their input/output schemas, and permission requirements.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
    HAS_RDFLIB = True
    # Namespaces - only available when rdflib is installed
    MCP = Namespace("http://antigravity.ai/ontology/mcp#")
    TOOL = Namespace("http://antigravity.ai/ontology/tool#")
    PERM = Namespace("http://antigravity.ai/ontology/permission#")
    CAP = Namespace("http://antigravity.ai/ontology/capability#")
except ImportError:
    HAS_RDFLIB = False
    MCP = TOOL = PERM = CAP = None
    Graph = Namespace = RDF = RDFS = OWL = XSD = Literal = URIRef = None


class OntologyManager:
    """
    Manages RDF graph for MCP tools, capabilities and permissions.
    Provides methods to register tools and query the semantic model.
    """
    
    def __init__(self):
        if not HAS_RDFLIB:
            logger.warning("rdflib not installed. Using in-memory fallback.")
            self._tools_data: Dict[str, Dict] = {}
            self.graph = None
        else:
            self.graph = Graph()
            self._bind_namespaces()
            self._load_base_ontologies()
            self._tools_data = {}
    
    def _bind_namespaces(self):
        """Bind common namespaces to the graph."""
        self.graph.bind("mcp", MCP)
        self.graph.bind("tool", TOOL)
        self.graph.bind("perm", PERM)
        self.graph.bind("cap", CAP)
    
    def _load_base_ontologies(self):
        """Load base ontology definitions."""
        # Tool class
        self.graph.add((TOOL.Tool, RDF.type, OWL.Class))
        self.graph.add((TOOL.Tool, RDFS.label, Literal("MCP Tool")))
        self.graph.add((TOOL.Tool, RDFS.comment, Literal("Executable function exposed via MCP")))
        
        # Tool properties
        self.graph.add((TOOL.name, RDF.type, OWL.DatatypeProperty))
        self.graph.add((TOOL.name, RDFS.domain, TOOL.Tool))
        self.graph.add((TOOL.name, RDFS.range, XSD.string))
        
        self.graph.add((TOOL.description, RDF.type, OWL.DatatypeProperty))
        self.graph.add((TOOL.description, RDFS.domain, TOOL.Tool))
        self.graph.add((TOOL.description, RDFS.range, XSD.string))
        
        self.graph.add((TOOL.requiredScope, RDF.type, OWL.ObjectProperty))
        self.graph.add((TOOL.requiredScope, RDFS.domain, TOOL.Tool))
        self.graph.add((TOOL.requiredScope, RDFS.range, PERM.Scope))
        
        # Permission classes
        self.graph.add((PERM.Scope, RDF.type, OWL.Class))
        self.graph.add((PERM.Role, RDF.type, OWL.Class))
        self.graph.add((PERM.hasScope, RDF.type, OWL.ObjectProperty))
        self.graph.add((PERM.hasScope, RDFS.domain, PERM.Role))
        self.graph.add((PERM.hasScope, RDFS.range, PERM.Scope))
        
        # Define base scopes
        self._define_scopes()
        self._define_roles()
    
    def _define_scopes(self):
        """Define available permission scopes."""
        scopes = [
            ("AuditRead", "audit:read"),
            ("AuditWrite", "audit:write"),
            ("ReportRead", "report:read"),
            ("ReportGenerate", "report:generate"),
            ("UserManage", "user:manage"),
        ]
        for scope_id, label in scopes:
            scope_uri = PERM[scope_id]
            self.graph.add((scope_uri, RDF.type, PERM.Scope))
            self.graph.add((scope_uri, RDFS.label, Literal(label)))
    
    def _define_roles(self):
        """Define user roles with their scopes."""
        # Auditor role
        self.graph.add((PERM.Auditor, RDF.type, PERM.Role))
        self.graph.add((PERM.Auditor, RDFS.label, Literal("Auditor")))
        self.graph.add((PERM.Auditor, PERM.hasScope, PERM.AuditRead))
        self.graph.add((PERM.Auditor, PERM.hasScope, PERM.AuditWrite))
        self.graph.add((PERM.Auditor, PERM.hasScope, PERM.ReportRead))
        
        # Admin role
        self.graph.add((PERM.Admin, RDF.type, PERM.Role))
        self.graph.add((PERM.Admin, RDFS.label, Literal("Administrator")))
        self.graph.add((PERM.Admin, PERM.hasScope, PERM.AuditRead))
        self.graph.add((PERM.Admin, PERM.hasScope, PERM.AuditWrite))
        self.graph.add((PERM.Admin, PERM.hasScope, PERM.ReportRead))
        self.graph.add((PERM.Admin, PERM.hasScope, PERM.ReportGenerate))
        self.graph.add((PERM.Admin, PERM.hasScope, PERM.UserManage))
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        scope: str
    ):
        """Register a tool in the RDF graph."""
        # Store in memory dict for quick access
        self._tools_data[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "outputSchema": output_schema,
            "requiredScope": scope
        }
        
        if self.graph is None:
            return
        
        # Add to RDF graph
        tool_uri = TOOL[name]
        self.graph.add((tool_uri, RDF.type, TOOL.Tool))
        self.graph.add((tool_uri, TOOL.name, Literal(name)))
        self.graph.add((tool_uri, TOOL.description, Literal(description)))
        self.graph.add((tool_uri, TOOL.requiredScope, PERM[scope]))
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool metadata by name."""
        return self._tools_data.get(name)
    
    def list_tools(self) -> list:
        """List all registered tools."""
        return list(self._tools_data.values())
    
    def query(self, sparql_query: str):
        """Execute a SPARQL query on the graph."""
        if self.graph is None:
            raise RuntimeError("SPARQL not available: rdflib not installed")
        return self.graph.query(sparql_query)
    
    def check_role_has_scope(self, role: str, scope: str) -> bool:
        """Check if a role has a specific scope using SPARQL."""
        if self.graph is None:
            # Fallback: simple permission check
            role_scopes = {
                "Admin": ["AuditRead", "AuditWrite", "ReportRead", "ReportGenerate", "UserManage"],
                "Auditor": ["AuditRead", "AuditWrite", "ReportRead"],
            }
            return scope in role_scopes.get(role, [])
        
        query = f"""
        PREFIX perm: <http://antigravity.ai/ontology/permission#>
        ASK {{
            perm:{role} perm:hasScope perm:{scope} .
        }}
        """
        result = self.graph.query(query)
        return bool(result.askAnswer)
    
    def serialize(self, format: str = "turtle") -> str:
        """Serialize the graph to a string."""
        if self.graph is None:
            return ""
        return self.graph.serialize(format=format)


# Global instance
_ontology_manager: Optional[OntologyManager] = None


def get_ontology_manager() -> OntologyManager:
    """Get or create the global ontology manager instance."""
    global _ontology_manager
    if _ontology_manager is None:
        _ontology_manager = OntologyManager()
    return _ontology_manager
