from django.apps import AppConfig


class McpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mcp'
    verbose_name = 'Model Context Protocol'

    def ready(self):
        # Import tools to register them
        from . import audit_tools  # noqa: F401
