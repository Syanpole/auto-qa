from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.audit.services import log_event
from apps.common.permissions import IsSuperAdmin, IsAdmin
from .models import DatasetVersion, TrainingJob, ModelRegistry, ModelAccess, StationModelAssignment
from .serializers import (
    DatasetVersionSerializer,
    TrainingJobSerializer,
    ModelRegistrySerializer,
    ModelAccessSerializer,
    StationModelAssignmentSerializer,
)
from .tasks import run_training_job


class DatasetVersionViewSet(viewsets.ModelViewSet):
    queryset = DatasetVersion.objects.all().order_by("-created_at")
    serializer_class = DatasetVersionSerializer
    permission_classes = [IsAdmin]


class TrainingJobViewSet(viewsets.ModelViewSet):
    queryset = TrainingJob.objects.select_related("dataset").all().order_by("-created_at")
    serializer_class = TrainingJobSerializer
    permission_classes = [IsAdmin]


class ModelRegistryViewSet(viewsets.ModelViewSet):
    queryset = ModelRegistry.objects.all().order_by("-created_at")
    serializer_class = ModelRegistrySerializer
    permission_classes = [IsSuperAdmin]


class ModelAccessViewSet(viewsets.ModelViewSet):
    queryset = ModelAccess.objects.select_related("user", "model").all().order_by("-created_at")
    serializer_class = ModelAccessSerializer
    permission_classes = [IsAdmin]


class StationModelAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StationModelAssignment.objects.select_related("station", "product", "model").all().order_by("-created_at")
    serializer_class = StationModelAssignmentSerializer
    permission_classes = [IsAdmin]


@api_view(["POST"])
@permission_classes([IsSuperAdmin])
def enqueue_training(request):
    serializer = TrainingJobSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = serializer.save()
    log_event(
        user=request.user if request.user.is_authenticated else None,
        action_type="retraining_triggered",
        target_object=str(job.id),
        metadata={"dataset_id": str(job.dataset_id)},
        request=request,
    )
    run_training_job.delay(str(job.id))
    return Response({"job_id": job.id, "status": "queued"}, status=202)


@api_view(["POST"])
@permission_classes([IsSuperAdmin])
def deploy_model(request, pk):
    model = ModelRegistry.objects.get(pk=pk)
    model.status = "production"
    model.promoted_at = timezone.now()
    model.save()
    log_event(user=request.user, action_type="model_deployed", target_object=model.model_name, metadata={"version": model.version_tag}, request=request)
    return Response({"status": "deployed", "model_id": model.id})
