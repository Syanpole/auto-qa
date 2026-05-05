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
    ai_models,
    ai_model_upload,
    ai_model_activate,
    ai_model_detail,
    model_exports,
    model_deployments,
)

router = DefaultRouter()
router.register("datasets", DatasetVersionViewSet, basename="dataset")
router.register("training/jobs", TrainingJobViewSet, basename="training-job")
router.register("models", ModelRegistryViewSet, basename="model")
router.register("model-access", ModelAccessViewSet, basename="model-access")
router.register("model-assignments", StationModelAssignmentViewSet, basename="model-assignment")

urlpatterns = [
    path("", include(router.urls)),
    path("training/ai-models/", ai_models),
    path("training/ai-models/upload/", ai_model_upload),
    path("training/ai-models/<uuid:model_uuid>/activate/", ai_model_activate),
    path("training/ai-models/<uuid:model_uuid>/", ai_model_detail),
    path("training/exports/", model_exports),
    path("training/deployments/", model_deployments),
    path("training/jobs/enqueue", enqueue_training),
    path("models/<uuid:pk>/deploy", deploy_model),
]
