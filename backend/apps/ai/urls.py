from django.urls import path
from .views import realtime_inference, batch_inference, health

urlpatterns = [
    path("inference/realtime", realtime_inference),
    path("inference/batch", batch_inference),
    path("health", health),
]
