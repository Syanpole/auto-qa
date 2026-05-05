"""
Django admin configuration for AI app models.
Allows model registration and inference audit log viewing in Django admin.
"""
from django.contrib import admin
from .models import InferenceModel, InferenceAuditLog


@admin.register(InferenceModel)
class InferenceModelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'version', 'is_active', 'is_enabled', 
        'confidence_threshold', 'last_activated_at', 'created_at'
    ]
    list_filter = ['is_active', 'is_enabled', 'model_format', 'created_at']
    search_fields = ['name', 'description', 'architecture']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_activated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'version', 'architecture', 'description')
        }),
        ('File & Format', {
            'fields': ('file_path', 'model_format', 'created_at', 'updated_at')
        }),
        ('Model Configuration', {
            'fields': ('confidence_threshold', 'iou_threshold', 'num_classes', 'input_shape')
        }),
        ('Status', {
            'fields': ('is_active', 'is_enabled', 'last_activated_at', 'last_used_at')
        }),
        ('Deployment', {
            'fields': ('deployed_by', 'deployment_notes', 'training_dataset')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override to set deployed_by user on creation."""
        if not change:  # Creating new model
            obj.deployed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InferenceAuditLog)
class InferenceAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'model_name', 'verdict', 'detection_count', 
        'inference_time_ms', 'user', 'station_id', 'created_at'
    ]
    list_filter = [
        'verdict', 'model_name', 'created_at', 'station_id'
    ]
    search_fields = ['model_name', 'station_id', 'product_id', 'user__username', 'image_hash']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'image_hash', 'metadata'
    ]
    
    fieldsets = (
        ('Request Details', {
            'fields': ('id', 'model', 'model_name', 'user', 'created_at')
        }),
        ('Station & Product', {
            'fields': ('station_id', 'product_id')
        }),
        ('Inference Results', {
            'fields': ('verdict', 'detection_count', 'confidence_threshold', 'inference_time_ms')
        }),
        ('Image & Metadata', {
            'fields': ('image_hash', 'metadata')
        }),
    )
    
    def has_add_permission(self, request):
        """Audit logs are read-only; created only via API."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs are read-only."""
        return False
