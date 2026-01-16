"""
MCP Tools for Audits module.

Exposes audit operations as MCP-compatible tools that can be discovered
and executed by any MCP client.
"""
from typing import Dict, Any
import logging

from .tools import ToolRegistry

logger = logging.getLogger(__name__)


@ToolRegistry.register(
    name="list_audits",
    description="List all audits with optional filters. Returns audit records including title, status, dates and metadata.",
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "planned"],
                "description": "Filter by audit status"
            },
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "Filter audits starting on or after this date (YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "Filter audits starting on or before this date (YYYY-MM-DD)"
            },
            "search": {
                "type": "string",
                "description": "Search term for title or description"
            },
            "auditor_id": {
                "type": "string",
                "description": "Filter by auditor's User ID (UUID)"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
                "description": "Maximum number of audits to return"
            },
            "offset": {
                "type": "integer",
                "default": 0,
                "minimum": 0,
                "description": "Number of audits to skip for pagination"
            }
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "audits": {"type": "array"},
            "total": {"type": "integer"}
        }
    },
    scope="AuditRead"
)
def list_audits(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """List audits with optional filtering."""
    from audits.models import Audit
    from audits.serializers import AuditSerializer
    from django.db.models import Q
    
    qs = Audit.objects.filter(deleted=False)
    
    # Apply status filter
    if status := params.get("status"):
        qs = qs.filter(status=status)
        
    # Apply date filters (filtering by start_date)
    if start_date := params.get("start_date"):
        qs = qs.filter(start_date__gte=start_date)
        
    if end_date := params.get("end_date"):
        qs = qs.filter(start_date__lte=end_date)
        
    # Apply search filter
    if search := params.get("search"):
        qs = qs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
        
    # Apply auditor filter
    if auditor_id := params.get("auditor_id"):
        qs = qs.filter(auditor_id=auditor_id)
    
    # Get total count before pagination
    total = qs.count()
    
    # Apply pagination
    limit = params.get("limit", 10)
    offset = params.get("offset", 0)
    qs = qs[offset:offset + limit]
    
    # Serialize
    serializer = AuditSerializer(qs, many=True)
    
    return {
        "audits": serializer.data,
        "total": total
    }


@ToolRegistry.register(
    name="get_audit_statistics",
    description="Get statistics about audits, including counts by status and total. Useful for dashboard summaries or answering 'how many' questions.",
    input_schema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "Filter stats for audits starting on or after this date"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "Filter stats for audits starting on or before this date"
            },
            "auditor_id": {
                "type": "string",
                "description": "Filter stats by auditor's User ID (UUID)"
            }
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "total": {"type": "integer"},
            "by_status": {"type": "object"}
        }
    },
    scope="AuditRead"
)
def get_audit_statistics(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Get audit statistics."""
    from audits.models import Audit
    from django.db.models import Count
    
    qs = Audit.objects.filter(deleted=False)
    
    if start_date := params.get("start_date"):
        qs = qs.filter(start_date__gte=start_date)
        
    if end_date := params.get("end_date"):
        qs = qs.filter(start_date__lte=end_date)
        
    if auditor_id := params.get("auditor_id"):
        qs = qs.filter(auditor_id=auditor_id)
        
    total = qs.count()
    
    # Count by status
    status_counts = qs.values('status').annotate(count=Count('id')).order_by('status')
    by_status = {item['status']: item['count'] for item in status_counts}
    
    return {
        "total": total,
        "by_status": by_status
    }


@ToolRegistry.register(
    name="get_audit",
    description="Get detailed information about a specific audit by ID, including events and evidences.",
    input_schema={
        "type": "object",
        "required": ["audit_id"],
        "properties": {
            "audit_id": {
                "type": "string",
                "format": "uuid",
                "description": "UUID of the audit to retrieve"
            }
        }
    },
    output_schema={"$ref": "#/definitions/Audit"},
    scope="AuditRead"
)
def get_audit(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Get a single audit by ID."""
    from audits.models import Audit
    from audits.serializers import AuditDetailSerializer
    
    audit_id = params.get("audit_id")
    
    try:
        audit = Audit.objects.get(id=audit_id, deleted=False)
    except Audit.DoesNotExist:
        raise ValueError(f"Audit with ID '{audit_id}' not found")
    
    serializer = AuditDetailSerializer(audit)
    return serializer.data


@ToolRegistry.register(
    name="create_audit",
    description="Create a new audit record with the specified title and description.",
    input_schema={
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {
                "type": "string",
                "minLength": 5,
                "maxLength": 255,
                "description": "Title of the audit"
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the audit"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "planned"],
                "default": "pending",
                "description": "Initial status of the audit"
            },
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "Start date (YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "End date (YYYY-MM-DD)"
            }
        }
    },
    output_schema={"$ref": "#/definitions/Audit"},
    scope="AuditWrite"
)
def create_audit(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new audit."""
    from audits.models import Audit
    from audits.serializers import AuditSerializer
    
    # Prepare data
    data = {
        "title": params.get("title"),
        "description": params.get("description", ""),
        "status": params.get("status", "pending"),
    }
    
    if start_date := params.get("start_date"):
        data["start_date"] = start_date
    if end_date := params.get("end_date"):
        data["end_date"] = end_date
    
    serializer = AuditSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    
    # Save with user context
    user = context.get("user")
    audit = serializer.save()
    
    # Log action
    try:
        from core.services import audit_logger
        audit_logger.log_action(
            collection_name="Audit",
            action="CREATE",
            data=serializer.data,
            user=user,
            resource_id=str(audit.id)
        )
    except Exception as e:
        logger.warning(f"Failed to log audit creation: {e}")
    
    return AuditSerializer(audit).data


@ToolRegistry.register(
    name="update_audit",
    description="Update an existing audit's properties.",
    input_schema={
        "type": "object",
        "required": ["audit_id"],
        "properties": {
            "audit_id": {
                "type": "string",
                "format": "uuid",
                "description": "UUID of the audit to update"
            },
            "title": {
                "type": "string",
                "minLength": 5,
                "maxLength": 255,
                "description": "New title"
            },
            "description": {
                "type": "string",
                "description": "New description"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "planned"],
                "description": "New status"
            }
        }
    },
    output_schema={"$ref": "#/definitions/Audit"},
    scope="AuditWrite"
)
def update_audit(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing audit."""
    from audits.models import Audit
    from audits.serializers import AuditSerializer
    
    audit_id = params.pop("audit_id")
    
    try:
        audit = Audit.objects.get(id=audit_id, deleted=False)
    except Audit.DoesNotExist:
        raise ValueError(f"Audit with ID '{audit_id}' not found")
    
    serializer = AuditSerializer(audit, data=params, partial=True)
    serializer.is_valid(raise_exception=True)
    audit = serializer.save()
    
    # Log action
    try:
        from core.services import audit_logger
        audit_logger.log_action(
            collection_name="Audit",
            action="UPDATE",
            data=params,
            user=context.get("user"),
            resource_id=str(audit.id)
        )
    except Exception as e:
        logger.warning(f"Failed to log audit update: {e}")
    
    return AuditSerializer(audit).data


@ToolRegistry.register(
    name="delete_audit",
    description="Soft delete an audit (marks as deleted, does not remove from database).",
    input_schema={
        "type": "object",
        "required": ["audit_id"],
        "properties": {
            "audit_id": {
                "type": "string",
                "format": "uuid",
                "description": "UUID of the audit to delete"
            }
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"}
        }
    },
    scope="AuditWrite"
)
def delete_audit(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Soft delete an audit."""
    from audits.models import Audit
    
    audit_id = params.get("audit_id")
    
    try:
        audit = Audit.objects.get(id=audit_id, deleted=False)
    except Audit.DoesNotExist:
        raise ValueError(f"Audit with ID '{audit_id}' not found")
    
    audit.delete()  # Uses soft delete from SoftDeleteModel
    
    # Log action
    try:
        from core.services import audit_logger
        audit_logger.log_action(
            collection_name="Audit",
            action="DELETE",
            data={"audit_id": audit_id},
            user=context.get("user"),
            resource_id=str(audit.id)
        )
    except Exception as e:
        logger.warning(f"Failed to log audit deletion: {e}")
    
    return {
        "success": True,
        "message": f"Audit '{audit.title}' deleted successfully"
    }


@ToolRegistry.register(
    name="list_audit_types",
    description="List all available audit types.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    output_schema={
        "type": "array",
        "items": {"$ref": "#/definitions/AuditType"}
    },
    scope="AuditRead"
)
def list_audit_types(params: Dict[str, Any], context: Dict[str, Any]) -> list:
    """List all audit types."""
    from audits.models import AuditType
    from audits.serializers import AuditTypeSerializer
    
    types = AuditType.objects.filter(deleted=False)
    serializer = AuditTypeSerializer(types, many=True)
    return serializer.data
