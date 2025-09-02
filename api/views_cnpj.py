from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from core.services.cnpj import fetch_cnpj
from core.models import Cliente

class CNPJLookupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        cnpj = request.query_params.get("cnpj")
        if not cnpj:
            return Response({"detail": "Informe o parâmetro ?cnpj="}, status=400)
        try:
            data = fetch_cnpj(cnpj)
            return Response({"ok": True, "data": data})
        except Exception as e:
            return Response({"ok": False, "error": str(e)}, status=400)

class ClienteFromCNPJView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        cnpj = (request.data.get("cnpj") or "").strip()
        if not cnpj:
            return Response({"detail": "Envie 'cnpj' no corpo."}, status=400)
        try:
            data = fetch_cnpj(cnpj)
        except Exception as e:
            return Response({"detail": f"Consulta falhou: {e}"}, status=400)

        nome = data.get("nome_fantasia") or data.get("razao_social") or ""
        cidade = data.get("municipio") or ""
        uf = data.get("uf") or ""

        cli, created = Cliente.objects.get_or_create(
            cnpj=data["cnpj"],
            defaults={
                "codigo": data["cnpj"][-6:],
                "nome": nome,
                "cidade": cidade,
                "uf": uf,
            },
        )

        changed = False
        if not cli.nome and nome:
            cli.nome = nome; changed = True
        if cidade and cli.cidade != cidade:
            cli.cidade = cidade; changed = True
        if uf and cli.uf != uf:
            cli.uf = uf; changed = True
        if changed:
            cli.save()

        return Response({"id": cli.id, "created": created})
