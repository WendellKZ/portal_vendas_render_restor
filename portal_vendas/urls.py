# portal_vendas/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API REST
    path("api/", include("api.urls")),

    # Login/Logout do DRF (para usar o botão "Login" na UI do /api/)
    path("api-auth/", include("rest_framework.urls")),

    # App do portal
    path("app/", include(("core.urls_front", "portal"), namespace="portal")),
]
