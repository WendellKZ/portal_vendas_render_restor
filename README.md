# Portal Vendas — Deploy no Render

## Deploy
1. Suba este código para um repositório GitHub.
2. No Render: New → Web Service → conecte ao repositório.
   - Build Command: `bash render-build.sh`
   - Start Command: `gunicorn portal_vendas.wsgi:application`
3. Adicione recurso PostgreSQL no Render → vincule ao serviço → Render injeta `DATABASE_URL`.
4. Variáveis de ambiente:
   - DJANGO_SECRET_KEY = uma string segura
   - DEBUG = 0
   - ALLOWED_HOSTS = *
5. Deploy.
