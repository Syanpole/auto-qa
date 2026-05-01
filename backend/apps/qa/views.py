from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from apps.audit.services import log_event
from apps.common.permissions import IsAdmin, IsSuperAdmin, IsQaOperator
from .models import QAStation, ProductProfile, StationThreshold, DefectEvent
from .serializers import (
    QAStationSerializer,
    ProductProfileSerializer,
    StationThresholdSerializer,
    DefectEventSerializer,
)


class QAStationViewSet(viewsets.ModelViewSet):
    queryset = QAStation.objects.all().order_by("station_code")
    serializer_class = QAStationSerializer
    permission_classes = [IsAdmin]


class ProductProfileViewSet(viewsets.ModelViewSet):
    queryset = ProductProfile.objects.all().order_by("product_code")
    serializer_class = ProductProfileSerializer
    permission_classes = [IsAdmin]


class StationThresholdViewSet(viewsets.ModelViewSet):
    queryset = StationThreshold.objects.select_related("station", "product").all()
    serializer_class = StationThresholdSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        threshold = serializer.save(updated_by=self.request.user)
        log_event(user=self.request.user, action_type="confidence_threshold_changed", target_object=str(threshold.id), metadata={"station_id": str(threshold.station_id), "product_id": str(threshold.product_id), "confidence_threshold": str(threshold.confidence_threshold)}, request=self.request)

    def perform_update(self, serializer):
        threshold = serializer.save(updated_by=self.request.user)
        log_event(user=self.request.user, action_type="confidence_threshold_changed", target_object=str(threshold.id), metadata={"station_id": str(threshold.station_id), "product_id": str(threshold.product_id), "confidence_threshold": str(threshold.confidence_threshold)}, request=self.request)


class DefectEventViewSet(viewsets.ModelViewSet):
    queryset = DefectEvent.objects.select_related("station", "product", "recorded_by").all().order_by("-event_ts")
    serializer_class = DefectEventSerializer
    filterset_fields = ["station", "product", "result", "defect_class", "lot_number"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.groups.filter(name__in=["super_admin", "admin"]).exists()):
            return queryset
        return queryset.filter(recorded_by=self.request.user)

    def perform_create(self, serializer):
        defect = serializer.save(recorded_by=self.request.user)
        log_event(user=self.request.user, action_type="pass_reject_decision", target_object=str(defect.id), metadata={"result": defect.result, "defect_class": defect.defect_class, "confidence": str(defect.confidence)}, request=self.request)


@api_view(["POST"])
def record_defect_decision(request, pk):
    defect = DefectEvent.objects.get(pk=pk)
    if not (request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name__in=["super_admin", "admin", "qa_operator"]).exists())):
        raise PermissionDenied("Not authorized to record defect decision.")
    defect.operator_action = request.data.get("operator_action", defect.operator_action)
    defect.final_disposition = request.data.get("final_disposition", defect.final_disposition)
    defect.override_reason = request.data.get("override_reason", defect.override_reason)
    defect.reviewed_by = request.user
    defect.reviewed_at = timezone.now()
    defect.save(update_fields=["operator_action", "final_disposition", "override_reason", "reviewed_by", "reviewed_at", "updated_at"])
    log_event(user=request.user, action_type="inference_override", target_object=str(defect.id), metadata={"final_disposition": defect.final_disposition, "operator_action": defect.operator_action}, request=request)
    return Response({"status": "updated", "defect_id": defect.id})


@api_view(["GET"])
def shift_report(request):
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        DefectEvent.objects.filter(event_ts__gte=start)
        .values("defect_class", "result")
        .annotate(total=Count("id"))
        .order_by("defect_class", "result")
    )
    return Response({"generated_at": now, "rows": list(rows)})


@api_view(["POST"])
def export_report(request):
    header = "event_ts,station,product,lot_number,defect_class,confidence,result\n"
    lines = [header]
    for event in DefectEvent.objects.all().order_by("-event_ts")[:10000]:
        lines.append(
            f"{event.event_ts},{event.station.station_code},{event.product.product_code},"
            f"{event.lot_number},{event.defect_class},{event.confidence},{event.result}\n"
        )
    response = HttpResponse("".join(lines), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=defect_report.csv"
    return response
