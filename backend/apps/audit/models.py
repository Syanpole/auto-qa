import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel


class ImmutableQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs are immutable and cannot be deleted through ORM operations.")


class ImmutableManager(models.Manager):
    def get_queryset(self):
        return ImmutableQuerySet(self.model, using=self._db)


class AuditLog(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action_type = models.CharField(max_length=120, db_index=True)
    action_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    target_object = models.CharField(max_length=255, blank=True, db_index=True)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    workstation_id = models.CharField(max_length=120, blank=True)
    remarks = models.TextField(blank=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ["-action_timestamp"]
        permissions = [("export_audit_log", "Can export audit logs")]
        indexes = [
            models.Index(fields=["-action_timestamp"]),
            models.Index(fields=["action_type", "-action_timestamp"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("Audit logs are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs are immutable and cannot be deleted.")
