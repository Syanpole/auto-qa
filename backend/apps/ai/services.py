import requests
from django.conf import settings
from django.utils import timezone
from apps.training.services import resolve_station_model, user_can_access_model
from apps.audit.services import log_event


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


def invoke_inference(payload: dict) -> dict:
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
    if not assignment:
        return _error_response("No active model assignment found for this station and product.", payload)
    if not user_can_access_model(request_user, assignment.model):
        return _error_response("User is not authorized for the requested model.", payload)

    payload = dict(payload)
    payload["model_id"] = str(assignment.model_id)
    payload["confidence_threshold"] = float(assignment.confidence_threshold)
    payload["nms_threshold"] = float(assignment.nms_threshold)
    log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_started", target_object=str(assignment.model_id), metadata={"station_code": station_code, "product_code": product_code}, request=request)
    try:
        result = invoke_inference(payload)
    except requests.RequestException as exc:
        return _error_response(f"Inference service unavailable: {exc}", payload)

    log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_completed", target_object=str(assignment.model_id), metadata={"verdict": result.get("verdict"), "latency_ms": result.get("latency_ms")}, request=request)
    return result
