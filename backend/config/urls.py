from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.qa.urls")),
    path("api/v1/", include("apps.ai.urls")),
    path("api/v1/", include("apps.training.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.live.urls")),
]
