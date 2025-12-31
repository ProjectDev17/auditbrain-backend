from django.contrib import admin
from .models import Audit

@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'created_by', 'created_at', 'deleted')
    list_filter = ('status', 'deleted', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('title', 'description', 'status')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('deleted', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )
