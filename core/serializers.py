from rest_framework import serializers
from .models import Cliente, Produto, TabelaDePreco, Preco, Pedido, ItemPedido

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = "__all__"

class TabelaDePrecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TabelaDePreco
        fields = "__all__"

class PrecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preco
        fields = "__all__"

class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = "__all__"
        read_only_fields = ("subtotal",)

    def validate(self, data):
        if data["qtd"] <= 0:
            raise serializers.ValidationError("Quantidade deve ser > 0")
        if data["preco_unit"] < 0:
            raise serializers.ValidationError("Preço unitário inválido")
        if data["desconto"] < 0 or data["desconto"] > 100:
            raise serializers.ValidationError("Desconto deve estar entre 0 e 100")
        return data

class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ("total",)

    def recalc_total(self, instance: Pedido):
        total = sum(i.subtotal for i in instance.itens.all())
        instance.total = total
        instance.save(update_fields=["total"])

    def create(self, validated_data):
        pedido = super().create(validated_data)
        self.recalc_total(pedido)
        return pedido

    def update(self, instance, validated_data):
        pedido = super().update(instance, validated_data)
        self.recalc_total(pedido)
        return pedido

