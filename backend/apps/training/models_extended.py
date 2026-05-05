"""
Extended model registry for YOLO integration and model lifecycle management.
"""
import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel
from apps.qa.models import QAStation, ProductProfile
from .models import AIModel


class ModelExport(TimeStampedModel):
    """
    Track model exports to different formats (ONNX, TensorRT, OpenVINO, etc).
    Supports benchmark comparison and rollback.
    """
    FORMAT_CHOICES = (
        ("onnx", "ONNX"),
        ("tensorrt", "TensorRT Engine"),
        ("openvino", "OpenVINO"),
        ("torchscript", "TorchScript"),
    )
    
    STATUS_CHOICES = (
        ("pending", "Pending Export"),
        ("exporting", "Exporting"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name="exports")
    export_format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    # Export metadata
    export_file_path = models.CharField(max_length=512, blank=True)
    export_file_size_mb = models.FloatField(default=0.0)
    export_params_json = models.JSONField(default=dict, help_text="Export parameters (quantization, optimization level)")
    
    # Benchmark data
    inference_time_ms = models.FloatField(default=0.0, help_text="Benchmark inference time")
    throughput_fps = models.FloatField(default=0.0, help_text="Benchmark throughput")
    memory_usage_mb = models.FloatField(default=0.0, help_text="Peak memory usage during inference")
    benchmark_hardware = models.CharField(max_length=120, default="RTX 4090", help_text="Hardware used for benchmarking")
    
    # Status tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    exported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("ai_model", "export_format")
        ordering = ["-created_at"]
        permissions = [("benchmark_export", "Can benchmark model exports")]

    def __str__(self):
        return f"{self.ai_model.model_name} -> {self.export_format}"


class ModelDeployment(TimeStampedModel):
    """
    Track model deployment history with rollback capability.
    """
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("rolled_back", "Rolled Back"),
    )

    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name="deployments")
    deployment_target = models.CharField(
        max_length=50,
        help_text="Target deployment location (e.g., 'production', 'staging', 'station_A')"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    # Deployment tracking
    deployed_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    
    # Deployment metrics
    inference_requests_count = models.IntegerField(default=0, help_text="Total inference requests processed")
    error_count = models.IntegerField(default=0, help_text="Failed inference requests")
    
    deployed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-deployed_at"]
        permissions = [("deploy_model", "Can deploy model")]
        indexes = [
            models.Index(fields=["ai_model", "status"]),
            models.Index(fields=["deployment_target", "status"]),
        ]

    def __str__(self):
        return f"{self.ai_model.model_name} -> {self.deployment_target} ({self.status})"


class ModelBenchmark(TimeStampedModel):
    """
    Store benchmark results for model comparison and optimization tracking.
    """
    HARDWARE_CHOICES = (
        ("rtx_4090", "NVIDIA RTX 4090"),
        ("rtx_3090", "NVIDIA RTX 3090"),
        ("a100", "NVIDIA A100"),
        ("cpu", "CPU (Intel/AMD)"),
        ("edge_device", "Edge Device (Jetson/TPU)"),
    )

    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name="benchmarks")
    export_format = models.CharField(max_length=20, default="pt", help_text="Format used for benchmark")
    hardware = models.CharField(max_length=30, choices=HARDWARE_CHOICES, default="rtx_4090")
    
    # Performance metrics
    inference_time_ms = models.FloatField(help_text="Average inference time (ms)")
    throughput_fps = models.FloatField(help_text="Maximum throughput (FPS)")
    min_latency_ms = models.FloatField(help_text="Minimum latency (ms)")
    max_latency_ms = models.FloatField(help_text="Maximum latency (ms)")
    p95_latency_ms = models.FloatField(help_text="95th percentile latency (ms)")
    memory_usage_mb = models.FloatField(help_text="Peak memory usage (MB)")
    
    # Test parameters
    batch_size = models.IntegerField(default=1)
    image_resolution = models.CharField(max_length=20, default="640x640")
    num_test_samples = models.IntegerField(default=1000)
    
    # Metadata
    benchmark_notes = models.TextField(blank=True)
    run_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("ai_model", "export_format", "hardware")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ai_model", "hardware"]),
            models.Index(fields=["export_format", "throughput_fps"]),
        ]

    def __str__(self):
        return f"{self.ai_model.model_name} ({self.export_format}) on {self.hardware}: {self.throughput_fps:.1f} FPS"
