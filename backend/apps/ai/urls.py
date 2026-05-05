from django.urls import path
from .views import realtime_inference, batch_inference, health, infer, snapshot, disposition, stats

urlpatterns = [
    path("inference/realtime", realtime_inference),
    path("inference/batch", batch_inference),
    path("health", health),
    path("ai/infer", infer),
    path("ai/snapshot", snapshot),
    path("ai/disposition", disposition),
    path("ai/stats", stats),
]
