from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # API do seu app
    path("api/", include("api.urls")),

    # Login do Django REST Framework (útil para testar APIs pelo browser)
    path("api-auth/", include("rest_framework.urls")),

    # Front do portal
    path("app/", include(("core.urls_front", "portal"), namespace="portal")),
]
