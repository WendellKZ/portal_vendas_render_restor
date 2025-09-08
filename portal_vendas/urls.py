from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls")),  # login UI do DRF

    # Front
    path("app/", include(("core.urls_front", "portal"), namespace="portal")),
]
