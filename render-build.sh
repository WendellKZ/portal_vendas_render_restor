#!/usr/bin/env bash
set -o errexit

# 1) Dependências
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 2) Migrações
python manage.py migrate --noinput

# 3) Garantir/atualizar superusuário (sem Shell)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo ">> Ensuring superuser: $DJANGO_SUPERUSER_USERNAME"
  python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","portal_vendas.settings")
import django
django.setup()
from django.contrib.auth import get_user_model
U = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
u, created = U.objects.get_or_create(username=username, defaults={"email": email})
u.email = email
u.is_staff = True
u.is_superuser = True
u.set_password(password)  # força/atualiza a senha
u.save()
print("Superuser", username, "created" if created else "updated")
PY
fi

# 4) Estáticos
python manage.py collectstatic --noinput


