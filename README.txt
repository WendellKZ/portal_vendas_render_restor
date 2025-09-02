PATCH Relatórios + XLSX/PDF + MTD/YTD + Heatmap + Simulador + Job Demo

1) Copie/cole os arquivos deste zip na raiz do seu projeto (vai sobrescrever api/urls.py e criar/atualizar api/views_reports.py e requirements.txt).
2) git add api/urls.py api/views_reports.py requirements.txt
   git commit -m "feat: relatórios completos + exportações + simulador + job demo"
   git push origin main
3) No Render: Manual Deploy → Deploy latest commit.

Endpoints:
- /api/relatorios/vendas-resumo/ (?de=YYYY-MM-DD&ate=YYYY-MM-DD&format=[json|csv|xlsx|pdf])
- /api/relatorios/itens-mais-vendidos/ (?de=...&ate=...&top=N&format=[json|csv|xlsx|pdf])
- /api/relatorios/mtd-ytd/
- /api/relatorios/heatmap-uf/ (?de=...&ate=...)
- /api/simulador/calcular/ (POST JSON: {tabela, items:[{sku,qtd}, ...]})
- /api/jobs/run-demo/ (POST JSON: {nome})

Login JWT:
- POST /api/auth/login/  body: {"username":"admin","password":"admin123"}
- Em todas as chamadas, envie: Header Authorization: Bearer <access>
