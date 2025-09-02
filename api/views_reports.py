
from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import Pedido, ItemPedido, Representante, Produto, Preco
from django.http import HttpResponse
import csv
import io

# ---------- Helpers ----------
def _parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        d = datetime.fromisoformat(date_str).date()
        return d
    except ValueError:
        return None

def _daterange_to_aware_start_end(de_str: str | None, ate_str: str | None):
    tz = timezone.get_current_timezone()
    de_date = _parse_date(de_str)
    ate_date = _parse_date(ate_str)
    if de_date:
        start = tz.localize(datetime.combine(de_date, time(0, 0, 0)))
    else:
        today = timezone.localdate()
        start = tz.localize(datetime.combine(today.replace(day=1), time(0, 0, 0)))
    if ate_date:
        end = tz.localize(datetime.combine(ate_date, time(23, 59, 59)))
    else:
        end = timezone.now()
    return start, end

def _restrict_by_user(qs, user):
    if user.is_staff:
        return qs
    try:
        rep = Representante.objects.get(user=user)
        return qs.filter(representante=rep)
    except Representante.DoesNotExist:
        return qs.none()

# ---------- Vendas Resumo ----------
class VendasResumoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        de = request.query_params.get("de")
        ate = request.query_params.get("ate")
        rep_codigo = request.query_params.get("rep")
        cliente_id = request.query_params.get("cliente")
        status_f = request.query_params.get("status")
        fmt = (request.query_params.get("format") or "").lower()

        start, end = _daterange_to_aware_start_end(de, ate)
        qs = Pedido.objects.select_related("cliente", "representante").filter(
            criado_em__gte=start, criado_em__lte=end
        )
        qs = _restrict_by_user(qs, request.user)
        if rep_codigo:
            qs = qs.filter(representante__codigo=rep_codigo)
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if status_f:
            qs = qs.filter(status=status_f)

        total_vendido = qs.aggregate(s=Coalesce(Sum("total"), Value(0)))["s"] or Decimal("0")
        qtd_pedidos = qs.aggregate(c=Count("id"))["c"] or 0
        ticket_medio = (total_vendido / qtd_pedidos) if qtd_pedidos else Decimal("0")

        por_cliente = list(
            qs.values("cliente_id", "cliente__nome")
              .annotate(total=Coalesce(Sum("total"), Value(0)), pedidos=Count("id"))
              .order_by("-total")
        )

        if fmt == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = "attachment; filename=vendas_resumo.csv"
            w = csv.writer(resp); w.writerow(["cliente_id", "cliente_nome", "pedidos", "total"])
            for row in por_cliente:
                w.writerow([row["cliente_id"], row["cliente__nome"], row["pedidos"], row["total"]])
            return resp
        elif fmt == "xlsx":
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active; ws.title = "Resumo"
            ws.append(["cliente_id", "cliente_nome", "pedidos", "total"])
            for row in por_cliente:
                ws.append([row["cliente_id"], row["cliente__nome"], row["pedidos"], float(row["total"])])
            buf = io.BytesIO(); wb.save(buf); buf.seek(0)
            resp = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = "attachment; filename=vendas_resumo.xlsx"
            return resp
        elif fmt == "pdf":
            from reportlab.pdfgen import canvas
            buf = io.BytesIO(); c = canvas.Canvas(buf); c.setFont("Helvetica", 12)
            c.drawString(40, 800, "Resumo de Vendas"); y = 780
            for row in por_cliente[:60]:
                line = f"{row['cliente__nome']}  | pedidos={row['pedidos']}  | total=R$ {row['total']}"
                c.drawString(40, y, line[:115]); y -= 18
                if y < 40: c.showPage(); y = 800
            c.save(); buf.seek(0)
            resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
            resp["Content-Disposition"] = "attachment; filename=vendas_resumo.pdf"
            return resp

        data = {
            "periodo": {"inicio": start.isoformat(), "fim": end.isoformat()},
            "filtros": {"rep": rep_codigo, "cliente": cliente_id, "status": status_f},
            "totais": {
                "qtd_pedidos": qtd_pedidos,
                "total_vendido": str(total_vendido),
                "ticket_medio": str(ticket_medio.quantize(Decimal('0.01'))),
            },
            "por_cliente": por_cliente,
        }
        return Response(data)

# ---------- Itens mais vendidos ----------
class ItensMaisVendidosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        de = request.query_params.get("de")
        ate = request.query_params.get("ate")
        top = int(request.query_params.get("top") or 20)
        fmt = (request.query_params.get("format") or "").lower()

        start, end = _daterange_to_aware_start_end(de, ate)
        pedidos = Pedido.objects.filter(criado_em__gte=start, criado_em__lte=end)
        pedidos = _restrict_by_user(pedidos, request.user)

        itens = (
            ItemPedido.objects.select_related("produto", "pedido")
            .filter(pedido__in=pedidos)
            .values("produto_id", "produto__sku", "produto__descricao")
            .annotate(
                qtd_total=Coalesce(Sum("qtd"), Value(0)),
                valor_total=Coalesce(Sum(F("qtd") * F("preco_unit") - Coalesce(F("desconto"), Value(0))), Value(0)),
            )
            .order_by("-qtd_total")[:top]
        )
        rows = list(itens)

        if fmt == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = "attachment; filename=itens_mais_vendidos.csv"
            w = csv.writer(resp)
            w.writerow(["produto_id", "sku", "descricao", "qtd_total", "valor_total"])
            for r in rows:
                w.writerow([r["produto_id"], r["produto__sku"], r["produto__descricao"], r["qtd_total"], r["valor_total"]])
            return resp
        elif fmt == "xlsx":
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active; ws.title = "Itens"
            ws.append(["produto_id", "sku", "descricao", "qtd_total", "valor_total"])
            for r in rows:
                ws.append([r["produto_id"], r["produto__sku"], r["produto__descricao"], float(r["qtd_total"]), float(r["valor_total"])])
            buf = io.BytesIO(); wb.save(buf); buf.seek(0)
            resp = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = "attachment; filename=itens_mais_vendidos.xlsx"
            return resp
        elif fmt == "pdf":
            from reportlab.pdfgen import canvas
            buf = io.BytesIO(); c = canvas.Canvas(buf); c.setFont("Helvetica", 12)
            c.drawString(40, 800, "Itens mais vendidos"); y = 780
            for r in rows[:60]:
                line = f"{r['produto__sku']} - {r['produto__descricao']} | qtd={r['qtd_total']} | R$ {r['valor_total']}"
                c.drawString(40, y, line[:115]); y -= 18
                if y < 40: c.showPage(); y = 800
            c.save(); buf.seek(0)
            resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
            resp["Content-Disposition"] = "attachment; filename=itens_mais_vendidos.pdf"
            return resp

        return Response({
            "periodo": {"inicio": start.isoformat(), "fim": end.isoformat()},
            "top": top,
            "itens": rows,
        })

# ---------- MTD / YTD ----------
class MTDYTDView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        now = timezone.localtime()
        ano = int(request.query_params.get("ano") or now.year)
        mes = int(request.query_params.get("mes") or now.month)

        tz = timezone.get_current_timezone()
        ytd_ini = tz.localize(datetime(ano, 1, 1, 0, 0, 0))
        mtd_ini = tz.localize(datetime(ano, mes, 1, 0, 0, 0))
        ate = now

        qs = Pedido.objects.filter(criado_em__lte=ate)
        qs = _restrict_by_user(qs, request.user)

        ytd = qs.filter(criado_em__gte=ytd_ini).aggregate(total=Coalesce(Sum("total"), Value(0)))["total"] or Decimal("0")
        mtd = qs.filter(criado_em__gte=mtd_ini).aggregate(total=Coalesce(Sum("total"), Value(0)))["total"] or Decimal("0")

        serie = list(
            qs.filter(criado_em__year=ano)
              .annotate(mes=TruncMonth("criado_em"))
              .values("mes")
              .annotate(total=Coalesce(Sum("total"), Value(0)))
              .order_by("mes")
        )
        metas = [{"mes": r["mes"].date().isoformat(), "meta": (r["total"]*Decimal("1.1")).quantize(Decimal("0.01"))} for r in serie]

        return Response({
            "ano": ano, "mes": mes,
            "ytd": str(ytd.quantize(Decimal('0.01'))),
            "mtd": str(mtd.quantize(Decimal('0.01'))),
            "serie_mensal": [{"mes": r["mes"].date().isoformat(), "total": float(r["total"])} for r in serie],
            "metas": metas,
        })

# ---------- Heatmap por UF ----------
class HeatmapUFView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        de = request.query_params.get("de")
        ate = request.query_params.get("ate")
        start, end = _daterange_to_aware_start_end(de, ate)
        qs = Pedido.objects.filter(criado_em__gte=start, criado_em__lte=end)
        qs = _restrict_by_user(qs, request.user)
        dados = list(
            qs.values("cliente__uf")
              .annotate(total=Coalesce(Sum("total"), Value(0)))
              .order_by("-total")
        )
        return Response({"periodo": {"inicio": start.isoformat(), "fim": end.isoformat()}, "por_uf": dados})

# ---------- Simulador ----------
class SimuladorCalcularView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        tabela = (request.data.get("tabela") or "Padrão").strip()
        items = request.data.get("items") or []
        resultado = {"tabela": tabela, "itens": [], "total_bruto": "0.00", "total_desc": "0.00", "total_liq": "0.00"}
        total_bruto = Decimal("0"); total_desc = Decimal("0"); total_liq = Decimal("0")

        for it in items:
            sku = (it.get("sku") or "").strip()
            qtd = Decimal(str(it.get("qtd") or 0))
            try:
                prod = Produto.objects.get(sku=sku)
            except Produto.DoesNotExist:
                resultado["itens"].append({"sku": sku, "erro": "SKU não encontrado"})
                continue
            preco = Preco.objects.filter(produto=prod, tabela__nome=tabela).first() or Preco.objects.filter(produto=prod).first()
            if not preco:
                resultado["itens"].append({"sku": sku, "erro": "Preço não encontrado"})
                continue
            punit = Decimal(preco.preco).quantize(Decimal("0.01"))
            desconto_pct = Decimal("0")
            if qtd >= 100: desconto_pct = Decimal("12")
            elif qtd >= 50: desconto_pct = Decimal("8")
            elif qtd >= 10: desconto_pct = Decimal("5")
            bruto = (punit * qtd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            desc  = (bruto * (desconto_pct / Decimal("100"))).quantize(Decimal("0.01"))
            liq   = (bruto - desc).quantize(Decimal("0.01"))
            total_bruto += bruto; total_desc += desc; total_liq += liq
            resultado["itens"].append({
                "sku": sku, "descricao": prod.descricao,
                "qtd": float(qtd), "preco_unit": float(punit),
                "desconto_percent": float(desconto_pct),
                "valor_bruto": float(bruto), "valor_desconto": float(desc), "valor_liquido": float(liq),
            })
        resultado["total_bruto"] = str(total_bruto); resultado["total_desc"] = str(total_desc); resultado["total_liq"] = str(total_liq)
        return Response(resultado)

# ---------- Job Demo ----------
class JobRunDemoView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        nome = request.data.get("nome") or "Job demo"
        now = timezone.localtime()
        return Response({
            "job": nome,
            "status": "executado",
            "inicio": now.isoformat(),
            "fim": now.isoformat(),
            "logs": [
                "Conectando no Sankhya (demo)...",
                "Lendo 120 SKUs...",
                "Atualizando preços e saldos...",
                "Concluído sem erros."
            ]
        })
