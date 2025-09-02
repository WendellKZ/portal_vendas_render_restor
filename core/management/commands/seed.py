from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Representante, Cliente, Produto, TabelaDePreco, Preco

class Command(BaseCommand):
    help = "Cria dados de exemplo"

    def handle(self, *args, **options):
        # Admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("Superusuário admin/admin123 criado"))

        # Representante
        rep_user, _ = User.objects.get_or_create(username="rep1", defaults={"email":"rep1@example.com"})
        if not rep_user.has_usable_password():
            rep_user.set_password("rep123")
            rep_user.save()
        Representante.objects.get_or_create(user=rep_user, defaults={"codigo": "REP001", "ativo": True})

        # Cliente
        Cliente.objects.get_or_create(codigo="C001", defaults={"nome":"Cliente Teste", "uf":"SP"})

        # Produtos
        p1, _ = Produto.objects.get_or_create(sku="SKU-001", defaults={"descricao":"Produto 1"})
        p2, _ = Produto.objects.get_or_create(sku="SKU-002", defaults={"descricao":"Produto 2"})

        # Tabela e preços
        tab, _ = TabelaDePreco.objects.get_or_create(nome="Padrão", defaults={"ativa": True})
        Preco.objects.get_or_create(produto=p1, tabela=tab, defaults={"preco": 10.00})
        Preco.objects.get_or_create(produto=p2, tabela=tab, defaults={"preco": 20.00})

        self.stdout.write(self.style.SUCCESS("Seed concluído. Usuários: admin/admin123, rep1/rep123"))

