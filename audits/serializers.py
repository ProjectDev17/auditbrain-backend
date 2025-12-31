from rest_framework import serializers
from .models import Audit

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = [
            'id', 'title', 'description', 'status', 
            'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'created_by', 'updated_by', 
            'deleted', 'deleted_by'
        ]
