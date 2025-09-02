from rest_framework import serializers
from core.models import (
    Representante,
    Cliente,
    Produto,
    TabelaDePreco,
    Preco,
    Pedido,
    ItemPedido,
)

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "codigo", "nome", "cnpj", "cidade", "uf"]

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ["id", "sku", "descricao", "familia", "ativo"]

class TabelaDePrecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TabelaDePreco
        fields = ["id", "nome", "ativa"]

class PrecoSerializer(serializers.ModelSerializer):
    produto_sku = serializers.CharField(source="produto.sku", read_only=True)
    tabela_nome = serializers.CharField(source="tabela.nome", read_only=True)

    class Meta:
        model = Preco
        fields = ["id", "produto", "produto_sku", "tabela", "tabela_nome", "preco"]

class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_sku = serializers.CharField(write_only=True, required=False, allow_blank=True)
    produto_info = ProdutoSerializer(source="produto", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "produto", "produto_sku", "produto_info", "qtd", "preco_unit", "desconto", "subtotal"]

class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, write_only=True, required=False)
    itens = ItemPedidoSerializer(source="itempedido_set", many=True, read_only=True)
    tabela = serializers.CharField(write_only=True, required=False, allow_blank=True)
    representante_codigo = serializers.CharField(source="representante.codigo", read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id", "numero", "cliente", "representante", "representante_codigo",
            "status", "total", "criado_em", "tabela", "items", "itens"
        ]
        read_only_fields = ["total", "criado_em"]

    def _get_or_default_tabela(self, nome: str | None):
        if nome:
            try:
                return TabelaDePreco.objects.get(nome=nome)
            except TabelaDePreco.DoesNotExist:
                pass
        obj, _ = TabelaDePreco.objects.get_or_create(nome="Padrão", defaults={"ativa": True})
        return obj

    def _resolve_produto(self, item):
        prod = item.get("produto")
        sku = item.get("produto_sku")
        if prod:
            return prod
        if sku:
            return Produto.objects.get(sku=sku)
        raise serializers.ValidationError("Informe produto (id) ou produto_sku.")

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        tabela_nome = validated_data.pop("tabela", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not validated_data.get("representante") and user and user.is_authenticated:
            try:
                validated_data["representante"] = Representante.objects.get(user=user)
            except Representante.DoesNotExist:
                pass

        tabela = self._get_or_default_tabela(tabela_nome)
        pedido = Pedido.objects.create(**validated_data)

        total = 0
        created_items = []
        for raw in items_data:
            raw = dict(raw)
            produto = self._resolve_produto(raw)

            preco = Preco.objects.filter(produto=produto, tabela=tabela).first()
            if not preco:
                raise serializers.ValidationError(
                    f"Produto {produto.sku} não possui preço na tabela '{tabela.nome}'"
                )

            qtd = raw.get("qtd") or 1
            preco_unit = raw.get("preco_unit") or preco.preco
            desconto = raw.get("desconto") or 0

            item = ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                qtd=qtd,
                preco_unit=preco_unit,
                desconto=desconto,
            )
            subtotal = (item.qtd * item.preco_unit) - (item.desconto or 0)
            total += subtotal
            created_items.append(item)

        pedido.total = total
        if not pedido.numero:
            from datetime import datetime
            pedido.numero = "PV-" + datetime.now().strftime("%y%m%d%H%M%S")
        pedido.save(update_fields=["total", "numero"])

        pedido._created_items = created_items
        return pedido
