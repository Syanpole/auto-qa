from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel
from apps.qa.models import QAStation


class LiveScreenSession(TimeStampedModel):
    STATUS_CHOICES = (("pending", "Pending"), ("active", "Active"), ("closed", "Closed"), ("rejected", "Rejected"))

    station = models.ForeignKey(QAStation, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_sessions_requested")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="live_sessions_approved")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    room_name = models.CharField(max_length=120, unique=True)
    signaling_key = models.CharField(max_length=120, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = [("view_live_screen", "Can view live QA screens"), ("request_live_screen", "Can request live QA screens")]


class LiveScreenAccessEvent(TimeStampedModel):
    session = models.ForeignKey(LiveScreenSession, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict)
