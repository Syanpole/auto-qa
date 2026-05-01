import requests
from django.conf import settings
from apps.training.services import resolve_station_model, user_can_access_model
from apps.audit.services import log_event


def invoke_inference(payload: dict) -> dict:
    endpoint = f"{settings.ML_SERVICE_URL}/v1/infer"
    response = requests.post(endpoint, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def resolve_authorized_inference(request_user, request, payload: dict) -> dict:
    station_id = payload.get("station_id")
    product_id = payload.get("product_id")
    if not station_id or not product_id:
        raise ValueError("station_id and product_id are required for authorized inference.")

    assignment = resolve_station_model(station_id, product_id)
    if not assignment:
        raise PermissionError("No active model assignment found for this station and product.")
    if not user_can_access_model(request_user, assignment.model):
        raise PermissionError("User is not authorized for the requested model.")

    payload = dict(payload)
    payload["model_id"] = str(assignment.model_id)
    payload["confidence_threshold"] = float(assignment.confidence_threshold)
    payload["nms_threshold"] = float(assignment.nms_threshold)
    log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_started", target_object=str(assignment.model_id), metadata={"station_id": station_id, "product_id": product_id}, request=request)
    result = invoke_inference(payload)
    log_event(user=request_user if request_user and request_user.is_authenticated else None, action_type="inference_completed", target_object=str(assignment.model_id), metadata={"verdict": result.get("verdict"), "latency_ms": result.get("latency_ms")}, request=request)
    return result
