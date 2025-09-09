from pathlib import Path
import os

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Verifica saúde do app.\n"
        "- Cria superusuário admin/admin123 (ou ADMIN_PASSWORD do ambiente) se não existir.\n"
        "- Importa produtos de XLSX/CSV se a tabela estiver vazia (ou se usar --force-import)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="data/produtos_importacao.xlsx",
            help="Caminho do XLSX/CSV com os produtos (REF/SKU, DESCRICAO, PRECO...).",
        )
        parser.add_argument(
            "--force-import",
            action="store_true",
            help="Força a importação mesmo se já houver produtos no banco.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        # 1) Garantir superusuário
        User = get_user_model()
        admin_user = "admin"
        admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")

        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(
                username=admin_user,
                email="admin@example.com",
                password=admin_pass,
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Superusuário '{admin_user}' criado."))
        else:
            self.stdout.write("↺ Superusuário já existe; pulando criação.")

        # 2) Importar produtos automaticamente
        from core.models import Produto  # import local para evitar carregamento precoce

        total_produtos = Produto.objects.count()
        path = Path(opts["file"])
        force = opts["force_import"]

        if not force and total_produtos > 0:
            self.stdout.write(f"↺ Produtos existentes: {total_produtos}. Importação automática pulada.")
            return

        if not path.exists():
            self.stdout.write(self.style.WARNING(f"⚠ Arquivo não encontrado: {path}"))
            return

        # Reutiliza o comando já existente
        call_command("import_produtos", file=str(path))
        self.stdout.write(self.style.SUCCESS("✓ Importação automática finalizada."))
