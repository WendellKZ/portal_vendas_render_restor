# core/management/commands/import_produtos.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Produto
from pathlib import Path
import csv
import unicodedata

try:
    import openpyxl  # type: ignore
except Exception:  # pragma: no cover
    openpyxl = None

def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def norm_key(s: str) -> str:
    s = strip_accents(str(s or "")).strip().lower()
    for ch in (" ", ".", "-", "/", "\\"):
        s = s.replace(ch, "_")
    return s

def as_text(v) -> str:
    # Converte qualquer valor para string SEM perder 123.0 -> "123"
    if v is None:
        return ""
    s = str(v).strip()
    # openpyxl costuma trazer números como float
    if s.endswith(".0"):
        try:
            if float(s).is_integer():
                s = s[:-2]
        except Exception:
            pass
    # Evitar notação científica
    try:
        if "e" in s.lower():
            n = float(s)
            if n.is_integer():
                s = str(int(n))
            else:
                s = ("%.15f" % n).rstrip("0").rstrip(".")
    except Exception:
        pass
    return s

def as_decimal_text(v) -> str:
    # Retorna string decimal com ponto como separador
    if v is None or str(v).strip() == "":
        return "0"
    s = str(v).strip().replace(".", "").replace(",", ".")
    try:
        x = float(s)
        return f"{x:.2f}"
    except Exception:
        return "0"

class Command(BaseCommand):
    help = "Importa produtos a partir de XLSX ou CSV. Usa REF/SKU como chave (campo Produto.sku)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Caminho do XLSX/CSV")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")

        # Carregar linhas
        rows = []
        if path.suffix.lower() in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            if not openpyxl:
                raise CommandError("openpyxl não instalado. Adicione openpyxl no requirements ou use CSV.")
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb.active
            raw_headers = [c.value for c in next(ws.rows)]
            headers = [norm_key(h) for h in raw_headers]
            for r in ws.iter_rows(min_row=2):
                data = [c.value for c in r]
                rows.append({headers[i]: data[i] for i in range(len(headers))})
        else:
            # CSV (tenta detectar delimitador)
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t,|")
                except Exception:
                    dialect = csv.excel
                reader = csv.DictReader(f, dialect=dialect)
                for row in reader:
                    rows.append({norm_key(k): v for k, v in row.items()})

        # helper para ler por múltiplos nomes de coluna
        def get(row: dict, *keys):
            for k in keys:
                kk = norm_key(k)
                if kk in row and row[kk] not in (None, ""):
                    return row[kk]
            return None

        total = created = updated = 0
        for row in rows:
            total += 1
            # tenta ler REF/SKU/codigo...
            ref = as_text(get(row, "ref", "sku", "codigo", "código", "referencia", "referência"))
            descricao = as_text(get(row, "produto", "descricao", "descrição", "desc", "nome"))
            preco_txt = as_decimal_text(get(row, "preco", "preço", "valor"))

            if not ref:
                # pula linha sem REF
                continue

            defaults = {"descricao": descricao or ref}
            # Se o model tiver preco (DecimalField), tenta atualizar também:
            if hasattr(Produto, "preco"):
                try:
                    from decimal import Decimal
                    defaults["preco"] = Decimal(preco_txt)
                except Exception:
                    pass

            obj, was_created = Produto.objects.update_or_create(
                sku=ref, defaults=defaults
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finalizado. total={total} criados={created} atualizados={updated}"
            )
        )
