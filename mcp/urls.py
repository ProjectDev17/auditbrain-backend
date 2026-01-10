"""
URL configuration for MCP module.
"""
from django.urls import path
from .server import MCPServerView, DiscoveryView

app_name = 'mcp'

urlpatterns = [
    path('', MCPServerView.as_view(), name='server'),
    path('discover/', DiscoveryView.as_view(), name='discover'),
]
