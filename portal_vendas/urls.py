from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls")),  # UI do DRF (login/logout)
    path("app/", include(("core.urls_front", "portal"), namespace="portal")),
]

