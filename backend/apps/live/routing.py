from django.urls import path
from .consumers import LiveScreenConsumer

websocket_urlpatterns = [path("ws/live/<str:session_id>/", LiveScreenConsumer.as_asgi())]
