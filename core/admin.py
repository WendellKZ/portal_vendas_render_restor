from django.contrib import admin
from .models import (
    Representante,
    Cliente,
    Produto,
    TabelaDePreco,
    Preco,
    Pedido,
    ItemPedido,
)

@admin.register(Representante)
class RepresentanteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "user", "ativo")
    search_fields = ("codigo", "user__username", "user__first_name", "user__last_name")
    list_filter = ("ativo",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "cnpj", "cidade", "uf")
    search_fields = ("codigo", "nome", "cnpj")
    list_filter = ("uf",)

    # inclui o JS que adiciona o botão "Buscar CNPJ" e faz o autofill
    class Media:
        js = ("core/cnpj_lookup.js",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("sku", "descricao", "familia", "ativo")
    search_fields = ("sku", "descricao", "familia")
    list_filter = ("ativo", "familia")


@admin.register(TabelaDePreco)
class TabelaDePrecoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa")
    list_filter = ("ativa",)


@admin.register(Preco)
class PrecoAdmin(admin.ModelAdmin):
    list_display = ("produto", "tabela", "preco")
    list_filter = ("tabela", "produto")
    search_fields = ("produto__sku", "produto__descricao", "tabela__nome")


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "representante", "status", "total", "criado_em")
    list_filter = ("status", "representante")
    search_fields = ("numero", "cliente__nome", "representante__codigo")
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "produto", "qtd", "preco_unit", "desconto", "subtotal")
    search_fields = ("pedido__numero", "produto__sku", "produto__descricao")

    # --- Jobs Admin ---
from .models import Job, JobLog

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "status", "progress", "created_at", "started_at", "finished_at")
    list_filter = ("status", "type")
    search_fields = ("id", "name", "type")

@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ("job", "ts", "level", "message")
    list_filter = ("level",)
    search_fields = ("message", "job__id")

