"""
AI app models for model registry and inference tracking.
"""
import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel


class InferenceModel(TimeStampedModel):
    """
    Registry of inference models available in the system.
    Tracks model versions, paths, and activation history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True, db_index=True, help_text="e.g., ic_defect_v1")
    file_path = models.CharField(max_length=512, help_text="Path to .pt model file")
    model_format = models.CharField(max_length=50, default="pytorch", choices=[("pytorch", "PyTorch"), ("onnx", "ONNX"), ("tensorrt", "TensorRT")])
    is_active = models.BooleanField(default=False, db_index=True, help_text="Currently active for production inference")
    is_enabled = models.BooleanField(default=True, help_text="Whether model can be used")
    
    # Model configuration
    confidence_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.850)
    iou_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    
    # Metadata
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, blank=True, help_text="Model version tag (e.g., v1.0.0)")
    architecture = models.CharField(max_length=120, blank=True, help_text="Model architecture (e.g., YOLOv8n)")
    training_dataset = models.CharField(max_length=255, blank=True)
    num_classes = models.IntegerField(null=True, blank=True)
    input_shape = models.CharField(max_length=50, default="640x640", help_text="Input image shape")
    
    # Lifecycle tracking
    deployed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    deployment_notes = models.TextField(blank=True)
    last_activated_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_enabled"]),
            models.Index(fields=["name"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({'ACTIVE' if self.is_active else 'inactive'})"


class InferenceAuditLog(TimeStampedModel):
    """
    Audit trail for inference requests.
    Captures request details, model used, results, and latency.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(InferenceModel, on_delete=models.PROTECT, null=True, blank=True)
    model_name = models.CharField(max_length=120, db_index=True, help_text="Model name at time of inference")
    
    # Request details
    station_id = models.CharField(max_length=120, blank=True, db_index=True)
    product_id = models.CharField(max_length=120, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Inference results
    verdict = models.CharField(max_length=20, choices=[("PASS", "Pass"), ("REJECT", "Reject"), ("ERROR", "Error")], db_index=True)
    detection_count = models.IntegerField(default=0)
    confidence_threshold = models.DecimalField(max_digits=4, decimal_places=3)
    
    # Performance metrics
    inference_time_ms = models.DecimalField(max_digits=8, decimal_places=2, help_text="Inference latency in milliseconds")
    
    # Request metadata
    image_hash = models.CharField(max_length=64, blank=True, db_index=True, help_text="SHA256 of image for duplicate detection")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional request/response data")
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "-created_at"]),
            models.Index(fields=["verdict", "-created_at"]),
            models.Index(fields=["station_id", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.model_name} | {self.verdict} | {self.inference_time_ms}ms"
