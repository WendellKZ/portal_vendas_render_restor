from rest_framework import viewsets, permissions, filters
from core.models import Cliente, Produto, TabelaDePreco, Preco, Pedido, ItemPedido
from .serializers import (
    ClienteSerializer,
    ProdutoSerializer,
    TabelaDePrecoSerializer,
    PrecoSerializer,
    PedidoSerializer,
    ItemPedidoSerializer,
)

class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("nome")
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome", "cnpj", "codigo", "cidade", "uf"]

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all().order_by("sku")
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["sku", "descricao", "familia"]

class TabelaViewSet(viewsets.ModelViewSet):
    queryset = TabelaDePreco.objects.all().order_by("nome")
    serializer_class = TabelaDePrecoSerializer
    permission_classes = [IsStaffOrReadOnly]

class PrecoViewSet(viewsets.ModelViewSet):
    queryset = Preco.objects.select_related("produto", "tabela").all()
    serializer_class = PrecoSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["produto__sku", "produto__descricao", "tabela__nome"]

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.select_related("cliente", "representante").all().order_by("-criado_em")
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["numero", "cliente__nome", "representante__codigo"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        try:
            rep = user.representante
            return qs.filter(representante=rep)
        except Exception:
            return qs.none()

class ItemPedidoViewSet(viewsets.ModelViewSet):
    queryset = ItemPedido.objects.select_related("pedido", "produto").all()
    serializer_class = ItemPedidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["pedido__numero", "produto__sku", "produto__descricao"]
