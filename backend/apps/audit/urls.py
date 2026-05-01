from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, export_audit_logs, heartbeat

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [path("", include(router.urls))]
urlpatterns += [path("audit-logs/export", export_audit_logs), path("audit/heartbeat", heartbeat)]
