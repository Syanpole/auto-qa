from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from .services import resolve_authorized_inference
from apps.audit.services import log_event


@api_view(["POST"])
def realtime_inference(request):
    payload = request.data
    try:
        result = resolve_authorized_inference(request.user, request, payload)
    except (ValueError, PermissionError) as exc:
        raise ValidationError(str(exc)) if isinstance(exc, ValueError) else PermissionDenied(str(exc))
    return Response(result)


@api_view(["POST"])
def batch_inference(request):
    payload = dict(request.data)
    payload["mode"] = "batch"
    try:
        result = resolve_authorized_inference(request.user, request, payload)
    except (ValueError, PermissionError) as exc:
        raise ValidationError(str(exc)) if isinstance(exc, ValueError) else PermissionDenied(str(exc))
    log_event(user=request.user if request.user.is_authenticated else None, action_type="batch_inference", target_object=str(payload.get("station_id", "")), metadata={"mode": "batch"}, request=request)
    return Response(result, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "ai-api"})
