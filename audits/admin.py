from django.contrib import admin
from .models import Audit, AuditEvent, Evidence

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


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'audit', 'event_type', 'severity', 'occurred_at', 'created_by')
    list_filter = ('event_type', 'severity', 'occurred_at', 'created_at')
    search_fields = ('title', 'description', 'audit__title')
    readonly_fields = ('id', 'created_at', 'created_by', 'updated_at', 'updated_by')


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'audit', 'file_type', 'uploaded_at', 'created_by')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('title', 'description', 'audit__title')
    readonly_fields = ('id', 'file_type', 'uploaded_at', 'created_by', 'updated_by')
