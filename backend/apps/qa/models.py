from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel


class QAStation(TimeStampedModel):
    station_code = models.CharField(max_length=50, unique=True)
    station_name = models.CharField(max_length=120)
    line_name = models.CharField(max_length=120)
    camera_endpoint = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.station_code} - {self.station_name}"


class ProductProfile(TimeStampedModel):
    product_code = models.CharField(max_length=80, unique=True)
    product_name = models.CharField(max_length=120)
    package_type = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.product_code


class StationThreshold(TimeStampedModel):
    station = models.ForeignKey(QAStation, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductProfile, on_delete=models.CASCADE)
    confidence_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.850)
    nms_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("station", "product")


class DefectEvent(TimeStampedModel):
    RESULT_CHOICES = (("pass", "Pass"), ("fail", "Fail"), ("review", "Review"))
    DISPOSITION_CHOICES = (("rework", "Rework"), ("waste", "Waste"), ("acknowledged", "Acknowledged"))

    event_ts = models.DateTimeField()
    station = models.ForeignKey(QAStation, on_delete=models.PROTECT)
    product = models.ForeignKey(ProductProfile, on_delete=models.PROTECT)
    lot_number = models.CharField(max_length=120)
    wafer_or_strip_id = models.CharField(max_length=120, blank=True)
    unit_serial = models.CharField(max_length=120, blank=True)
    defect_class = models.CharField(max_length=120)
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    severity = models.CharField(max_length=50, blank=True)
    bbox_json = models.JSONField(default=dict)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    model_version = models.CharField(max_length=120)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="defect_events_recorded")
    image_uri = models.CharField(max_length=512)
    overlay_uri = models.CharField(max_length=512, blank=True)
    raw_meta_json = models.JSONField(default=dict)
    final_disposition = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, blank=True)
    operator_action = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_defects")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["station", "event_ts"]),
            models.Index(fields=["product", "defect_class", "event_ts"]),
            models.Index(fields=["result", "event_ts"]),
        ]
