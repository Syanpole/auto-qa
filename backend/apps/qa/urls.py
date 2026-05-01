from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    QAStationViewSet,
    ProductProfileViewSet,
    StationThresholdViewSet,
    DefectEventViewSet,
    shift_report,
    export_report,
    record_defect_decision,
)

router = DefaultRouter()
router.register("stations", QAStationViewSet, basename="station")
router.register("products", ProductProfileViewSet, basename="product")
router.register("thresholds", StationThresholdViewSet, basename="threshold")
router.register("defects", DefectEventViewSet, basename="defect")

urlpatterns = [
    path("", include(router.urls)),
    path("reports/shift", shift_report),
    path("reports/export", export_report),
    path("defects/<uuid:pk>/decision", record_defect_decision),
]
