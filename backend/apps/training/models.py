import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel
from apps.qa.models import QAStation, ProductProfile


class ModelRegistry(TimeStampedModel):
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
