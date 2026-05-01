from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import LiveScreenSessionViewSet, LiveScreenAccessEventViewSet, health, approve_live_session

router = DefaultRouter()
router.register("live/sessions", LiveScreenSessionViewSet, basename="live-session")
router.register("live/events", LiveScreenAccessEventViewSet, basename="live-event")

urlpatterns = [path("", include(router.urls)), path("live/health", health)]
urlpatterns += [path("live/sessions/<uuid:pk>/approve", approve_live_session)]
