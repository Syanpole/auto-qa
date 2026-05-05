from django.urls import path
from .views import (
    realtime_inference, batch_inference, health, infer, snapshot, disposition, stats,
    list_models, get_active_model, activate_model
)

urlpatterns = [
    path("inference/realtime", realtime_inference),
    path("inference/batch", batch_inference),
    path("health", health),
    path("ai/infer", infer),
    path("ai/snapshot", snapshot),
    path("ai/disposition", disposition),
    path("ai/stats", stats),
    
    # Model management endpoints
    path("models/list", list_models),
    path("models/active", get_active_model),
    path("models/activate", activate_model),
]
