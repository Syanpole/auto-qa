from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.audit.services import log_event
from apps.common.permissions import IsSuperAdmin, IsAdmin
from .models import DatasetVersion, TrainingJob, ModelRegistry, ModelAccess, StationModelAssignment, AIModel
from .models_extended import ModelExport, ModelDeployment
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


def _serialize_ai_model(model: AIModel) -> dict:
    return {
        "model_uuid": str(model.model_uuid),
        "model_name": model.model_name,
        "version_tag": model.version_tag,
        "framework": model.framework,
        "status": model.status,
        "is_active": model.is_active,
        "model_size_mb": model.model_size_mb,
        "throughput_fps": model.throughput_fps,
        "inference_time_ms": model.inference_time_ms,
        "metrics_json": model.metrics_json,
        "deployed_at": model.deployed_at.isoformat() if model.deployed_at else None,
        "training_completed_at": model.training_completed_at.isoformat() if model.training_completed_at else None,
    }


@api_view(["GET"])
def ai_models(request):
    models = AIModel.objects.all().order_by("-created_at")
    return Response({"results": [_serialize_ai_model(model) for model in models]})


@api_view(["POST"])
def ai_model_upload(request):
    uploaded_file = request.FILES.get("file")
    model = AIModel.objects.create(
        model_name=request.data.get("model_name") or (uploaded_file.name if uploaded_file else "unnamed-model"),
        version_tag=request.data.get("version_tag") or "1.0.0",
        framework=request.data.get("framework") or "ultralytics",
        primary_format="pt",
        pt_file_path=uploaded_file.name if uploaded_file else "",
        status="draft",
        is_active=False,
        metrics_json={},
        defect_types=[],
        notes=request.data.get("notes", ""),
    )
    return Response(_serialize_ai_model(model), status=201)


@api_view(["POST"])
def ai_model_activate(request, model_uuid):
    model = get_object_or_404(AIModel, model_uuid=model_uuid)
    AIModel.objects.filter(is_active=True).update(is_active=False)
    model.is_active = True
    model.status = "production"
    model.deployed_at = timezone.now()
    model.save(update_fields=["is_active", "status", "deployed_at", "updated_at"])
    return Response(_serialize_ai_model(model))


@api_view(["DELETE"])
def ai_model_detail(request, model_uuid):
    model = get_object_or_404(AIModel, model_uuid=model_uuid)
    model.delete()
    return Response(status=204)


@api_view(["GET", "POST"])
def model_exports(request):
    if request.method == "GET":
        exports = ModelExport.objects.select_related("ai_model").all().order_by("-created_at")
        return Response(
            {
                "results": [
                    {
                        "id": str(export.id),
                        "ai_model_id": str(export.ai_model_id),
                        "export_format": export.export_format,
                        "status": export.status,
                        "file_size_mb": export.export_file_size_mb,
                        "throughput_fps": export.throughput_fps,
                        "inference_time_ms": export.inference_time_ms,
                        "completed_at": export.completed_at.isoformat() if export.completed_at else None,
                    }
                    for export in exports
                ]
            }
        )

    ai_model_id = request.data.get("ai_model_id")
    export_format = request.data.get("export_format") or "onnx"
    ai_model = get_object_or_404(AIModel, model_uuid=ai_model_id)
    export = ModelExport.objects.create(
        ai_model=ai_model,
        export_format=export_format,
        status="completed",
        completed_at=timezone.now(),
        export_file_size_mb=0.0,
        export_params_json={},
        inference_time_ms=ai_model.inference_time_ms,
        throughput_fps=ai_model.throughput_fps,
    )
    return Response({"id": str(export.id), "status": export.status}, status=201)


@api_view(["GET", "POST"])
def model_deployments(request):
    if request.method == "GET":
        deployments = ModelDeployment.objects.select_related("ai_model").all().order_by("-deployed_at")
        return Response(
            {
                "results": [
                    {
                        "id": str(deployment.id),
                        "model_id": str(deployment.ai_model_id),
                        "deployment_target": deployment.deployment_target,
                        "status": deployment.status,
                        "inference_requests_count": deployment.inference_requests_count,
                        "error_count": deployment.error_count,
                        "deployed_at": deployment.deployed_at.isoformat(),
                    }
                    for deployment in deployments
                ]
            }
        )

    ai_model_id = request.data.get("ai_model_id")
    deployment_target = request.data.get("deployment_target") or "local"
    ai_model = get_object_or_404(AIModel, model_uuid=ai_model_id)
    deployment = ModelDeployment.objects.create(
        ai_model=ai_model,
        deployment_target=deployment_target,
        status="active",
        deployed_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"id": str(deployment.id), "status": deployment.status}, status=201)


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
