from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Cliente, Produto, TabelaDePreco, Preco, Pedido, ItemPedido
from .serializers import (
    ClienteSerializer, ProdutoSerializer, TabelaDePrecoSerializer,
    PrecoSerializer, PedidoSerializer, ItemPedidoSerializer
)

class DefaultPerm(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

class ClienteViewSet(DefaultPerm):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_fields = ["codigo", "nome", "cnpj"]

class ProdutoViewSet(DefaultPerm):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    search_fields = ["sku", "descricao", "familia"]

class TabelaDePrecoViewSet(DefaultPerm):
    queryset = TabelaDePreco.objects.all()
    serializer_class = TabelaDePrecoSerializer

class PrecoViewSet(DefaultPerm):
    queryset = Preco.objects.select_related("produto", "tabela").all()
    serializer_class = PrecoSerializer

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup_preco(self, request):
        """
        GET /api/precos/lookup?tabela=<id>&sku=ABC123
        Retorna: {"sku": "...", "tabela": "...", "preco": 10.50}
        """
        tabela_id = request.query_params.get("tabela")
        sku = request.query_params.get("sku")
        if not tabela_id or not sku:
            return Response({"detail": "Informe 'tabela' e 'sku'."}, status=400)
        try:
            produto = Produto.objects.get(sku=sku)
            tabela = TabelaDePreco.objects.get(id=tabela_id, ativa=True)
            preco = Preco.objects.get(produto=produto, tabela=tabela).preco
            return Response({"sku": sku, "tabela": tabela.nome, "preco": preco})
        except Produto.DoesNotExist:
            return Response({"detail": "Produto não encontrado."}, status=404)
        except TabelaDePreco.DoesNotExist:
            return Response({"detail": "Tabela não encontrada ou inativa."}, status=404)
        except Preco.DoesNotExist:
            return Response({"detail": "Preço não cadastrado para este SKU/tabela."}, status=404)

class PedidoViewSet(DefaultPerm):
    queryset = Pedido.objects.select_related("cliente", "representante").all()
    serializer_class = PedidoSerializer

    @action(detail=True, methods=["post"], url_path="enviar")
    def enviar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status != "RASCUNHO":
            return Response({"detail": "Somente rascunhos podem ser enviados."}, status=400)
        if not pedido.itens.exists():
            return Response({"detail": "Pedido sem itens."}, status=400)
        pedido.status = "ENVIADO"
        pedido.save(update_fields=["status"])
        return Response({"status": pedido.status})

    @action(detail=True, methods=["post"], url_path="aprovar")
    def aprovar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status != "ENVIADO":
            return Response({"detail": "Somente pedidos enviados podem ser aprovados."}, status=400)
        pedido.status = "APROVADO"
        pedido.save(update_fields=["status"])
        return Response({"status": pedido.status})

    @action(detail=True, methods=["post"], url_path="rejeitar")
    def rejeitar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status not in ("ENVIADO", "RASCUNHO"):
            return Response({"detail": "Apenas rascunho/enviado podem ser rejeitados."}, status=400)
        pedido.status = "REJEITADO"
        pedido.save(update_fields=["status"])
        return Response({"status": pedido.status})

class ItemPedidoViewSet(DefaultPerm):
    queryset = ItemPedido.objects.select_related("pedido", "produto").all()
    serializer_class = ItemPedidoSerializer

    def perform_create(self, serializer):
        item = serializer.save()
        # recalcula total do pedido
        p = item.pedido
        p.total = sum(i.subtotal for i in p.itens.all())
        p.save(update_fields=["total"])

    def perform_update(self, serializer):
        item = serializer.save()
        p = item.pedido
        p.total = sum(i.subtotal for i in p.itens.all())
        p.save(update_fields=["total"])

    def perform_destroy(self, instance):
        pedido = instance.pedido
        super().perform_destroy(instance)
        pedido.total = sum(i.subtotal for i in pedido.itens.all())
        pedido.save(update_fields=["total"])
