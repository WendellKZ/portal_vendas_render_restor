from datetime import datetime, time
from decimal import Decimal
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import Pedido, ItemPedido, Representante
from django.http import HttpResponse
import csv

# NEW: XLSX/PDF
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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

# Helpers de exportação --------------------------------------------------------

def _resp_csv(filename: str):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

def _resp_xlsx(filename: str):
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

def _resp_pdf(filename: str):
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

# Views ------------------------------------------------------------------------

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

        # EXPORTAÇÕES ---------------------------------------------------------
        if fmt == "csv":
            resp = _resp_csv("vendas_resumo.csv")
            w = csv.writer(resp)
            w.writerow(["cliente_id", "cliente_nome", "pedidos", "total"])
            for row in por_cliente:
                w.writerow([row["cliente_id"], row["cliente__nome"], row["pedidos"], row["total"]])
            return resp

        if fmt == "xlsx":
            resp = _resp_xlsx("vendas_resumo.xlsx")
            wb = Workbook()
            ws = wb.active
            ws.title = "Resumo"
            ws.append(["Período início", start.isoformat()])
            ws.append(["Período fim", end.isoformat()])
            ws.append([])
            ws.append(["Qtd Pedidos", "Total Vendido", "Ticket Médio"])
            ws.append([qtd_pedidos, float(total_vendido), float(ticket_medio)])
            ws.append([])
            ws.append(["Cliente ID", "Cliente", "Pedidos", "Total"])
            for r in por_cliente:
                ws.append([r["cliente_id"], r["cliente__nome"], r["pedidos"], float(r["total"])])
            wb.save(resp)
            return resp

        if fmt == "pdf":
            resp = _resp_pdf("vendas_resumo.pdf")
            c = canvas.Canvas(resp, pagesize=A4)
            w, h = A4
            y = h - 40
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Resumo de Vendas")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Período: {start:%d/%m/%Y} a {end:%d/%m/%Y}")
            y -= 20
            c.drawString(40, y, f"Qtd Pedidos: {qtd_pedidos}")
            y -= 15
            c.drawString(40, y, f"Total Vendido: R$ {total_vendido}")
            y -= 15
            c.drawString(40, y, f"Ticket Médio: R$ {ticket_medio.quantize(Decimal('0.01'))}")
            y -= 25
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, "Top clientes")
            y -= 18
            c.setFont("Helvetica", 9)
            for r in por_cliente[:30]:
                c.drawString(40, y, f'{r["cliente__nome"][:60]}')
                c.drawRightString(w-40, y, f'R$ {Decimal(r["total"]).quantize(Decimal("0.01"))}')
                y -= 14
                if y < 60:
                    c.showPage()
                    y = h - 40
            c.showPage()
            c.save()
            return resp

        # JSON ----------------------------------------------------------------
        data = {
            "periodo": {"inicio": start.isoformat(), "fim": end.isoformat()},
            "filtros": {"rep": rep_codigo, "cliente": cliente_id, "status": status_f},
            "totais": {
                "qtd_pedidos": qtd_pedidos,
                "total_vendido": float(total_vendido),
                "ticket_medio": float(ticket_medio.quantize(Decimal('0.01'))),
            },
            "por_cliente": por_cliente,
        }
        return Response(data)


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

        # EXPORTAÇÕES ---------------------------------------------------------
        if fmt == "csv":
            resp = _resp_csv("itens_mais_vendidos.csv")
            w = csv.writer(resp)
            w.writerow(["produto_id", "sku", "descricao", "qtd_total", "valor_total"])
            for r in rows:
                w.writerow([
                    r["produto_id"], r["produto__sku"], r["produto__descricao"],
                    float(r["qtd_total"]), float(r["valor_total"])
                ])
            return resp

        if fmt == "xlsx":
            resp = _resp_xlsx("itens_mais_vendidos.xlsx")
            wb = Workbook()
            ws = wb.active
            ws.title = "Itens"
            ws.append(["Período início", start.isoformat()])
            ws.append(["Período fim", end.isoformat()])
            ws.append([])
            ws.append(["Produto ID", "SKU", "Descrição", "Qtd", "Valor"])
            for r in rows:
                ws.append([
                    r["produto_id"], r["produto__sku"], r["produto__descricao"],
                    float(r["qtd_total"]), float(r["valor_total"])
                ])
            wb.save(resp)
            return resp

        # JSON ----------------------------------------------------------------
        return Response({
            "periodo": {"inicio": start.isoformat(), "fim": end.isoformat()},
            "top": top,
            "itens": rows,
        })
