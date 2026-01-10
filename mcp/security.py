"""
Security utilities for MCP.

Provides scope validation and permission checking using RDF ontologies.
"""
from typing import Optional, List
import logging

from .ontologies import get_ontology_manager

logger = logging.getLogger(__name__)


class ScopeValidator:
    """Validates user permissions against required scopes."""
    
    def __init__(self):
        self.ontology = get_ontology_manager()
    
    def get_user_role(self, user) -> str:
        """
        Determine user role from Django user object.
        
        Args:
            user: Django User instance
        
        Returns:
            Role name (Admin, Auditor, etc.)
        """
        if not user or not user.is_authenticated:
            return "Anonymous"
        
        if user.is_superuser:
            return "Admin"
        
        if user.is_staff:
            return "Auditor"
        
        # Check user groups for role mapping
        user_groups = user.groups.values_list('name', flat=True)
        
        if 'administrators' in user_groups or 'admin' in user_groups:
            return "Admin"
        if 'auditors' in user_groups or 'auditor' in user_groups:
            return "Auditor"
        
        return "Auditor"  # Default role
    
    def get_user_scopes(self, user) -> List[str]:
        """
        Get all scopes available to a user based on their role.
        
        Args:
            user: Django User instance
        
        Returns:
            List of scope names
        """
        role = self.get_user_role(user)
        
        role_scopes = {
            "Admin": ["AuditRead", "AuditWrite", "ReportRead", "ReportGenerate", "UserManage"],
            "Auditor": ["AuditRead", "AuditWrite", "ReportRead"],
            "Anonymous": [],
        }
        
        return role_scopes.get(role, [])
    
    def user_has_scope(self, user, required_scope: str) -> bool:
        """
        Check if user has the required scope.
        
        Args:
            user: Django User instance
            required_scope: Scope name to check
        
        Returns:
            True if user has scope, False otherwise
        """
        role = self.get_user_role(user)
        
        # Use ontology for SPARQL-based check if available
        try:
            return self.ontology.check_role_has_scope(role, required_scope)
        except Exception as e:
            logger.warning(f"Ontology check failed, using fallback: {e}")
            # Fallback to simple check
            user_scopes = self.get_user_scopes(user)
            return required_scope in user_scopes


def validate_scope(user, scope: str) -> bool:
    """
    Validate that a user has the required scope.
    
    Convenience function for quick scope validation.
    
    Args:
        user: Django User instance
        scope: Required scope name
    
    Returns:
        True if authorized, False otherwise
    """
    validator = ScopeValidator()
    return validator.user_has_scope(user, scope)


def get_user_scopes(user) -> List[str]:
    """
    Get all scopes for a user.
    
    Args:
        user: Django User instance
    
    Returns:
        List of scope names
    """
    validator = ScopeValidator()
    return validator.get_user_scopes(user)
