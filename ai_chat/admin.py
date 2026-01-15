from django.contrib import admin
from .models import AIConversation, AIMessage


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'timestamp', 'content_preview')
    list_filter = ('role', 'timestamp')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('id', 'timestamp')
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation')
