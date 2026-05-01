from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    DatasetVersionViewSet,
    TrainingJobViewSet,
    ModelRegistryViewSet,
    ModelAccessViewSet,
    StationModelAssignmentViewSet,
    enqueue_training,
    deploy_model,
)

router = DefaultRouter()
router.register("datasets", DatasetVersionViewSet, basename="dataset")
router.register("training/jobs", TrainingJobViewSet, basename="training-job")
router.register("models", ModelRegistryViewSet, basename="model")
router.register("model-access", ModelAccessViewSet, basename="model-access")
router.register("model-assignments", StationModelAssignmentViewSet, basename="model-assignment")

urlpatterns = [
    path("", include(router.urls)),
    path("training/jobs/enqueue", enqueue_training),
    path("models/<uuid:pk>/deploy", deploy_model),
]
