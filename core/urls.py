from rest_framework import routers
from .views import ClienteViewSet, ProdutoViewSet, TabelaDePrecoViewSet, PrecoViewSet, PedidoViewSet, ItemPedidoViewSet

router = routers.DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'produtos', ProdutoViewSet)
router.register(r'tabelas', TabelaDePrecoViewSet)
router.register(r'precos', PrecoViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'itens', ItemPedidoViewSet)

urlpatterns = router.urls

