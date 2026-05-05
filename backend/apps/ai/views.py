from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from .services import resolve_authorized_inference
from apps.audit.services import log_event
from apps.qa.models import QAStation, ProductProfile, DefectEvent
from django.utils import timezone


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


@api_view(["POST"])
def infer(request):
    """Alias endpoint used by frontend clients."""
    payload = request.data
    try:
        result = resolve_authorized_inference(request.user, request, payload)
    except (ValueError, PermissionError) as exc:
        raise ValidationError(str(exc)) if isinstance(exc, ValueError) else PermissionDenied(str(exc))
    return Response(result)


@api_view(["POST"])
def snapshot(request):
    """Persist a lightweight snapshot event for operator history."""
    station_code = request.data.get("station_id")
    product_code = request.data.get("product_id")
    if not station_code or not product_code:
        raise ValidationError("station_id and product_id are required.")

    try:
        station = QAStation.objects.get(station_code=station_code)
        product = ProductProfile.objects.get(product_code=product_code)
    except (QAStation.DoesNotExist, ProductProfile.DoesNotExist):
        raise ValidationError("Station or product not found.")

    defects_found = int(request.data.get("defects_found", 0))
    result = (request.data.get("result") or "review").lower()
    if result == "reject":
        result = "fail"
    if result not in {"pass", "fail", "review"}:
        result = "review"

    event = DefectEvent.objects.create(
        event_ts=timezone.now(),
        station=station,
        product=product,
        lot_number=request.data.get("lot_number") or "N/A",
        wafer_or_strip_id=request.data.get("wafer_or_strip_id", ""),
        unit_serial=request.data.get("unit_serial", ""),
        defect_class=(request.data.get("defect_class") or "capture")[:120],
        confidence=request.data.get("confidence", 0),
        severity=request.data.get("severity", ""),
        bbox_json=request.data.get("bbox_json", {}),
        result=result,
        model_version=request.data.get("model_used") or request.data.get("model_version") or "unknown",
        recorded_by=request.user if request.user.is_authenticated else None,
        image_uri=request.data.get("image_path") or request.data.get("image_uri") or "",
        overlay_uri=request.data.get("overlay_uri", ""),
        raw_meta_json={
            "defects_found": defects_found,
            "source": "snapshot",
            "timestamp": request.data.get("timestamp"),
        },
    )

    log_event(
        user=request.user if request.user.is_authenticated else None,
        action_type="snapshot_saved",
        target_object=str(event.id),
        metadata={"station_id": station_code, "product_id": product_code, "defects_found": defects_found},
        request=request,
    )
    return Response({"status": "saved", "defect_event_id": str(event.id)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def disposition(request):
    """Record operator disposition decision."""
    station_code = request.data.get("station_id")
    product_code = request.data.get("product_id")
    operator_action = (request.data.get("operator_action") or "").upper()
    if not station_code or not product_code or operator_action not in {"PASS", "REWORK", "SCRAP"}:
        raise ValidationError("station_id, product_id, and operator_action(PASS|REWORK|SCRAP) are required.")

    try:
        station = QAStation.objects.get(station_code=station_code)
        product = ProductProfile.objects.get(product_code=product_code)
    except (QAStation.DoesNotExist, ProductProfile.DoesNotExist):
        raise ValidationError("Station or product not found.")

    result_map = {"PASS": "pass", "REWORK": "review", "SCRAP": "fail"}
    disposition_map = {"PASS": "acknowledged", "REWORK": "rework", "SCRAP": "waste"}

    event = DefectEvent.objects.create(
        event_ts=timezone.now(),
        station=station,
        product=product,
        lot_number=request.data.get("lot_number") or "N/A",
        wafer_or_strip_id=request.data.get("wafer_or_strip_id", ""),
        unit_serial=request.data.get("unit_serial", ""),
        defect_class=(request.data.get("defect_class") or "operator_decision")[:120],
        confidence=request.data.get("confidence", 0),
        severity=request.data.get("severity", ""),
        bbox_json=request.data.get("bbox_json", {}),
        result=result_map[operator_action],
        model_version=request.data.get("model_used") or "unknown",
        recorded_by=request.user if request.user.is_authenticated else None,
        image_uri=request.data.get("image_path") or request.data.get("image_uri") or "",
        overlay_uri=request.data.get("overlay_uri", ""),
        raw_meta_json={"defects_found": int(request.data.get("defects_found", 0)), "source": "disposition"},
        final_disposition=disposition_map[operator_action],
        operator_action=disposition_map[operator_action],
        reviewed_by=request.user if request.user.is_authenticated else None,
        reviewed_at=timezone.now() if request.user.is_authenticated else None,
        override_reason=request.data.get("override_reason", ""),
    )

    log_event(
        user=request.user if request.user.is_authenticated else None,
        action_type="inference_override",
        target_object=str(event.id),
        metadata={"operator_action": operator_action, "station_id": station_code, "product_id": product_code},
        request=request,
    )
    return Response({"status": "recorded", "defect_event_id": str(event.id), "action": operator_action})


@api_view(["GET"])
def stats(request):
    """Return authenticated user's inference/disposition stats."""
    if not request.user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    base_qs = DefectEvent.objects.filter(recorded_by=request.user)
    total = base_qs.count()
    pass_count = base_qs.filter(result="pass").count()
    fail_count = base_qs.filter(result="fail").count()
    review_count = base_qs.filter(result="review").count()
    pass_rate = (pass_count / total * 100) if total else 0
    return Response(
        {
            "total_inferences": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "review_count": review_count,
            "pass_rate_percent": round(pass_rate, 2),
        }
    )


# ==================== Model Management Endpoints ====================

@api_view(["GET"])
def list_models(request):
    """List all registered inference models."""
    from .model_loader import ModelLoaderService
    models = ModelLoaderService.list_available_models()
    return Response({"models": models})


@api_view(["GET"])
def get_active_model(request):
    """Get the currently active production model."""
    from .model_loader import ModelLoaderService
    active_model = ModelLoaderService.get_active_model()
    if not active_model:
        return Response({"error": "No active model"}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        "model_id": str(active_model.id),
        "model_name": active_model.name,
        "file_path": active_model.file_path,
        "confidence_threshold": float(active_model.confidence_threshold),
        "iou_threshold": float(active_model.iou_threshold),
        "version": active_model.version,
        "architecture": active_model.architecture,
        "is_active": active_model.is_active,
    })


@api_view(["POST"])
def activate_model(request):
    """Activate a registered model for production inference."""
    if not request.user.is_staff:
        raise PermissionDenied("Only staff can activate models.")
    
    model_name = request.data.get("model_name")
    if not model_name:
        raise ValidationError("model_name is required.")
    
    try:
        from .model_loader import ModelLoaderService
        result = ModelLoaderService.activate_model(model_name)
        
        log_event(
            user=request.user,
            action_type="model_activated",
            target_object=model_name,
            metadata={"model_name": model_name},
            request=request
        )
        
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        raise ValidationError(str(e))

