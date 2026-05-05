import requests
import hashlib
from io import BytesIO
from base64 import b64decode
from django.conf import settings
from django.utils import timezone
from apps.training.services import resolve_station_model, user_can_access_model
from apps.audit.services import log_event
from .model_registry import get_registry
from .models import InferenceAuditLog

logger_import = __import__('logging').getLogger(__name__)


def _error_response(message: str, payload: dict) -> dict:
    return {
        "status": "error",
        "pass_fail_status": "ERROR",
        "detections": [],
        "detection_count": 0,
        "confidence_threshold": float(payload.get("confidence_threshold", 0.85)),
        "inference_time_ms": 0.0,
        "model_used": payload.get("model_name"),
        "error_message": message,
        "timestamp": timezone.now().isoformat(),
    }


def _log_inference_audit(
    model_name: str,
    result: dict,
    payload: dict,
    user = None
):
    """
    Log inference request to audit database.
    Non-blocking; errors are logged but don't fail the inference.
    """
    try:
        # Calculate image hash for duplicate detection
        image_hash = ""
        if payload.get("image_base64"):
            try:
                image_data = b64decode(payload["image_base64"])
                image_hash = hashlib.sha256(image_data).hexdigest()
            except:
                pass

        audit_user = user if getattr(user, "is_authenticated", False) else None
        
        InferenceAuditLog.objects.create(
            model_name=model_name,
            station_id=payload.get("station_id", ""),
            product_id=payload.get("product_id", ""),
            user=audit_user,
            verdict=result.get("pass_fail_status", "ERROR"),
            detection_count=result.get("detection_count", 0),
            confidence_threshold=payload.get("confidence_threshold", 0.85),
            inference_time_ms=result.get("inference_time_ms", 0),
            image_hash=image_hash,
            metadata={
                "defects": result.get("detections", []),
                "latency_ms": result.get("inference_time_ms"),
                "source": "api"
            }
        )
    except Exception as e:
        logger_import.warning(f"Failed to log inference audit: {str(e)}")


def invoke_inference(payload: dict) -> dict:
    """
    Invoke inference via ML service.
    Automatically uses active production model if not specified.
    """
    # Use active production model if not explicitly specified
    if not payload.get("model_name"):
        registry = get_registry()
        active_model = registry.get_active_model()
        payload = dict(payload)
        payload["model_name"] = active_model
    
    endpoint = f"{settings.ML_SERVICE_URL}/v1/infer"
    response = requests.post(endpoint, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def resolve_authorized_inference(request_user, request, payload: dict) -> dict:
    # Extract station and product codes from payload
    # Note: These are codes (e.g., 'Station-A', 'IC_001'), not database IDs
    station_code = payload.get("station_id")  # Frontend sends as 'station_id' but contains code
    product_code = payload.get("product_id")  # Frontend sends as 'product_id' but contains code

    if not station_code or not product_code:
        return _error_response("station_id and product_id are required for authorized inference.", payload)

    assignment = resolve_station_model(station_code, product_code)
    payload = dict(payload)

    if assignment:
        if not user_can_access_model(request_user, assignment.model):
            if not settings.DEBUG:
                return _error_response("User is not authorized for the requested model.", payload)
        else:
            payload["model_id"] = str(assignment.model_id)
            payload["confidence_threshold"] = float(assignment.confidence_threshold)
            payload["nms_threshold"] = float(assignment.nms_threshold)
            log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_started", target_object=str(assignment.model_id), metadata={"station_code": station_code, "product_code": product_code}, request=request)
    elif not settings.DEBUG:
        return _error_response("No active model assignment found for this station and product.", payload)

    try:
        result = invoke_inference(payload)
    except requests.RequestException as exc:
        return _error_response(f"Inference service unavailable: {exc}", payload)

    if assignment:
        log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_completed", target_object=str(assignment.model_id), metadata={"verdict": result.get("pass_fail_status"), "latency_ms": result.get("inference_time_ms")}, request=request)
    
    # Log inference audit
    model_name = result.get("model_used", payload.get("model_name", "unknown"))
    _log_inference_audit(model_name, result, payload, user=request_user)
    
    return result
