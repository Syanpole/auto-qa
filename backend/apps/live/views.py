from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.audit.services import log_event
from apps.common.permissions import IsSuperAdmin
from .models import LiveScreenSession, LiveScreenAccessEvent
from .serializers import LiveScreenSessionSerializer, LiveScreenAccessEventSerializer
from .permissions import CanRequestLiveScreen, CanViewLiveScreen


class LiveScreenSessionViewSet(viewsets.ModelViewSet):
    queryset = LiveScreenSession.objects.select_related("station", "requested_by", "approved_by").all().order_by("-created_at")
    serializer_class = LiveScreenSessionSerializer
    permission_classes = [CanRequestLiveScreen]

    def get_permissions(self):
        if self.action in {"list", "retrieve", "approve", "close"}:
            return [CanViewLiveScreen()]
        return [CanRequestLiveScreen()]

    def perform_create(self, serializer):
        session = serializer.save(requested_by=self.request.user, room_name=f"live-{timezone.now().timestamp()}")
        log_event(user=self.request.user, action_type="live_screen_request", target_object=str(session.id), metadata={"station_id": str(session.station_id)}, request=self.request)


@api_view(["POST"])
@permission_classes([CanViewLiveScreen])
def approve_live_session(request, pk):
    session = LiveScreenSession.objects.get(pk=pk)
    session.status = "active"
    session.approved_by = request.user
    session.save(update_fields=["status", "approved_by", "updated_at"])
    log_event(user=request.user, action_type="live_screen_approved", target_object=str(session.id), request=request)
    return Response({"status": "approved", "session_id": session.id, "room_name": session.room_name})


class LiveScreenAccessEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LiveScreenAccessEvent.objects.select_related("session", "actor").all().order_by("-created_at")
    serializer_class = LiveScreenAccessEventSerializer
    permission_classes = [IsSuperAdmin]


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "live-screen"})
