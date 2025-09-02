Pack UI (templates + static + rotas) — Portal de Vendas
======================================================

1) Copie o conteúdo deste ZIP para a raiz do projeto.
   - templates/*.html
   - core/static/portal/app.css, app.js
   - core/urls_front.py
   - core/views_front.py

2) Em portal_vendas/urls.py, inclua:
   from django.urls import path, include
   urlpatterns = [
       # ... demais rotas ...
       path('app/', include('core.urls_front')),
   ]

3) Faça commit e push para o Render:
   git add templates core/static/portal core/urls_front.py core/views_front.py portal_vendas/urls.py
   git commit -m "feat(ui): portal com charts (dashboard, mtdytd, heatmap, simulador)"
   git push origin main

Páginas:
- /app/                       (Dashboard: resumo + top itens)
- /app/relatorios/mtdytd/     (linhas MTD/YTD – requer endpoint /api/relatorios/mtd-ytd/)
- /app/relatorios/heatmap/    (barras por UF – requer /api/relatorios/heatmap-uf/)
- /app/simulador/             (POST /api/simulador/calcular/)

Login:
- Clique em "Login" (canto direito do topo)
- Informe admin / admin123 (ou credenciais do seu ambiente)
- O token JWT é salvo em localStorage e usado nos fetchs subsequentes.

Observações:
- Se algum endpoint de relatório não existir ainda, a página exibe uma dica e não quebra o layout.
- Chart.js via CDN.
