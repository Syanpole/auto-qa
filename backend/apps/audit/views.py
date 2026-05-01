from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.common.permissions import IsSuperAdmin
from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import log_event


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]


@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_audit_logs(request):
    rows = AuditLog.objects.all().order_by("-action_timestamp")[:50000]
    lines = ["action_timestamp,user,action_type,target_object,ip_address,workstation_id,remarks\n"]
    for row in rows:
        lines.append(
            f"{row.action_timestamp},{getattr(row.user, 'username', '')},{row.action_type},{row.target_object},"
            f"{row.ip_address or ''},{row.workstation_id},{row.remarks}\n"
        )
    response = HttpResponse("".join(lines), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=audit_logs.csv"
    return response


@api_view(["POST"])
def heartbeat(request):
    log_event(user=request.user if request.user.is_authenticated else None, action_type="api_heartbeat", request=request)
    return Response({"status": "ok"})
