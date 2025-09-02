from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from api.urls import urlpatterns as api_urls
import core.urls
import core.urls_front as ui_urls

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
            "rel_itens": "/api/relatorios/itens-mais-vendidos/",
            "rel_resumo": "/api/relatorios/vendas-resumo/",
            "app": "/app/"
        }
    })

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
    path('api/', include(core.urls)),
    path('app/', include(ui_urls)),  # <- UI do portal
]
