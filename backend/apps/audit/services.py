from django.conf import settings
from django.http import HttpRequest
from .models import AuditLog


def _extract_request_context(request: HttpRequest | None) -> dict:
    if not request:
        return {}
    return {
        "ip_address": request.META.get("REMOTE_ADDR", ""),
        "workstation_id": request.META.get("HTTP_X_WORKSTATION_ID", ""),
    }


def log_event(
    *,
    user=None,
    action_type: str,
    target_object: str = "",
    metadata: dict | None = None,
    remarks: str = "",
    request: HttpRequest | None = None,
) -> AuditLog:
    context = _extract_request_context(request)
    return AuditLog.objects.create(
        user=user,
        action_type=action_type,
        target_object=target_object,
        metadata=metadata or {},
        remarks=remarks,
        **context,
    )
