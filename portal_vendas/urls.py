from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from api.urls import urlpatterns as api_urls
import core.urls

def home(_):
    return JsonResponse({
        "app": "Portal Vendas",
        "status": "ok",
        "links": {
            "admin": "/admin/",
            "auth": "/api/auth/login/",
            "clientes": "/api/clientes/",
            "produtos": "/api/produtos/",
            "pedidos": "/api/pedidos/",
            "app": "/app/"
        }
    })

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
    path('api/', include(core.urls)),
    path('app/', include(('core.urls_front', 'portal'), namespace='portal')),
]
