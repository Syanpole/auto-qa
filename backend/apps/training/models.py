import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel
from apps.qa.models import QAStation, ProductProfile


class AIModel(TimeStampedModel):
    """
    Comprehensive YOLO model registry with full lifecycle tracking.
    Supports multiple export formats and deployment states.
    """
    FORMAT_CHOICES = (
        ("pt", "PyTorch (.pt)"),
        ("onnx", "ONNX"),
        ("tensorrt", "TensorRT Engine"),
        ("openvino", "OpenVINO"),
        ("torchscript", "TorchScript"),
    )
    
    DEFECT_TYPE_CHOICES = (
        ("scratch", "Scratch"),
        ("crack", "Crack"),
        ("chip", "Chip"),
        ("surface_defect", "Surface Defect"),
        ("generic", "Generic Defect"),
    )
    
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("training", "Training"),
        ("validated", "Validated"),
        ("production", "Production"),
        ("deprecated", "Deprecated"),
        ("archived", "Archived"),
    )

    # Core model identification
    model_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    model_name = models.CharField(max_length=120, help_text="Unique model identifier (e.g., 'IC_Defect_Detection_v1')")
    model_family = models.CharField(max_length=40, default="yolov8", help_text="Model architecture family")
    version_tag = models.CharField(max_length=80, help_text="Semantic version tag (e.g., '1.0.0')")
    
    # Defect detection capabilities
    defect_types = models.JSONField(
        default=list,
        help_text="List of defect classes trained on (e.g., ['scratch', 'crack', 'chip'])"
    )
    
    # File storage
    primary_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="pt")
    pt_file_path = models.CharField(max_length=512, blank=True, help_text="Path to .pt weights file")
    onnx_file_path = models.CharField(max_length=512, blank=True)
    tensorrt_file_path = models.CharField(max_length=512, blank=True)
    openvino_file_path = models.CharField(max_length=512, blank=True)
    torchscript_file_path = models.CharField(max_length=512, blank=True)
    
    # Metadata
    framework = models.CharField(max_length=40, default="ultralytics", help_text="Framework used (ultralytics, etc)")
    model_size_mb = models.FloatField(default=0.0, help_text="Model file size in MB")
    input_shape = models.JSONField(default=lambda: {"height": 640, "width": 640}, help_text="Expected input dimensions")
    
    # Performance metrics
    metrics_json = models.JSONField(
        default=dict,
        help_text="Training metrics (accuracy, precision, recall, F1, mAP50, mAP95)"
    )
    inference_time_ms = models.FloatField(default=0.0, help_text="Avg inference time (ms) on reference hardware")
    throughput_fps = models.FloatField(default=0.0, help_text="Max throughput (FPS) on reference hardware")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_active = models.BooleanField(default=False, help_text="Current active model for inference")
    
    # Deployment tracking
    deployed_at = models.DateTimeField(null=True, blank=True, help_text="When model moved to production")
    promoted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_models_promoted"
    )
    training_completed_at = models.DateTimeField(null=True, blank=True)
    
    # QA tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_models_created"
    )
    notes = models.TextField(blank=True, help_text="Training notes, calibration details, known limitations")
    
    class Meta:
        unique_together = ("model_name", "version_tag")
        ordering = ["-created_at"]
        permissions = [
            ("deploy_ai_model", "Can deploy AI model to production"),
            ("export_ai_model", "Can export AI model to other formats"),
            ("benchmark_ai_model", "Can run model benchmarks"),
        ]
        indexes = [
            models.Index(fields=["is_active", "status"]),
            models.Index(fields=["model_family", "status"]),
        ]

    def __str__(self):
        return f"{self.model_name} v{self.version_tag} ({self.status})"


class ModelRegistry(TimeStampedModel):
    """
    Legacy model registry - kept for backward compatibility.
    New code should use AIModel instead.
    """
    FAMILY_CHOICES = (("esmd_yolov26n", "ESMD-YOLOv26n"), ("rtdetr", "RT-DETR"))
    STATUS_CHOICES = (("draft", "Draft"), ("validated", "Validated"), ("production", "Production"), ("archived", "Archived"))

    model_name = models.CharField(max_length=120)
    model_family = models.CharField(max_length=40, choices=FAMILY_CHOICES)
    version_tag = models.CharField(max_length=80)
    framework = models.CharField(max_length=80, default="pytorch")
    weights_uri = models.CharField(max_length=512)
    onnx_uri = models.CharField(max_length=512, blank=True)
    tensorrt_uri = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    metrics_json = models.JSONField(default=dict)
    trained_at = models.DateTimeField(null=True, blank=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("model_name", "version_tag")
        permissions = [("deploy_model", "Can deploy model")]


class ModelAccess(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    model = models.ForeignKey(ModelRegistry, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="model_access_assigned_by")
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "model")
        permissions = [("grant_model_access", "Can grant model access")]


class StationModelAssignment(TimeStampedModel):
    station = models.ForeignKey(QAStation, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductProfile, on_delete=models.CASCADE)
    model = models.ForeignKey(ModelRegistry, on_delete=models.CASCADE)
    confidence_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.850)
    nms_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("station", "product")
        permissions = [("assign_station_model", "Can assign station model")]


class DatasetVersion(TimeStampedModel):
    dataset_name = models.CharField(max_length=120)
    version_tag = models.CharField(max_length=80)
    source_type = models.CharField(max_length=50, default="production_capture")
    class_distribution_json = models.JSONField(default=dict)
    storage_uri = models.CharField(max_length=512)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("dataset_name", "version_tag")


class TrainingJob(TimeStampedModel):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    dataset = models.ForeignKey(DatasetVersion, on_delete=models.PROTECT)
    base_model_ref = models.CharField(max_length=120)
    output_model_ref = models.CharField(max_length=120, blank=True)
    params_json = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    logs_uri = models.CharField(max_length=512, blank=True)
