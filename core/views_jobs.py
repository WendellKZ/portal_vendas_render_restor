
from __future__ import annotations
import threading, time, random
from typing import Callable
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status
from django.core.paginator import Paginator
from .models import Job, JobLog

# -----------------------------------------------------------------------------------
# Helpers de log e runner

def _log(job: Job, msg: str, level="INFO"):
    JobLog.objects.create(job=job, message=msg, level=level)

def _set_status(job: Job, status: str, progress: int | None = None, extra: dict | None = None):
    Job.objects.filter(pk=job.pk).update(
        status=status,
        progress=progress if progress is not None else job.progress,
        result=extra if extra is not None else job.result,
        started_at=job.started_at or (timezone.now() if status == Job.Status.RUNNING else job.started_at),
        finished_at=timezone.now() if status in (Job.Status.SUCCESS, Job.Status.ERROR) else None,
    )
    job.refresh_from_db()

def _run_steps(job: Job, steps: list[tuple[str, Callable[[], dict | None]]]):
    try:
        _set_status(job, Job.Status.RUNNING, 0)
        _log(job, f"Job iniciado: {job.name} ({job.type})")

        n = len(steps) or 1
        for i, (title, fn) in enumerate(steps, start=1):
            _log(job, f"Iniciando passo {i}/{n}: {title}")
            # simula processamento pesado
            result = fn() or {}
            _log(job, f"Concluído: {title} — {result}")
            prog = int(i * 100 / n)
            _set_status(job, Job.Status.RUNNING, prog)

        _set_status(job, Job.Status.SUCCESS, 100, extra={"ok": True})
        _log(job, "Job finalizado com sucesso", "INFO")

    except Exception as e:  # noqa
        _set_status(job, Job.Status.ERROR, extra={"error": str(e)})
        _log(job, f"Erro: {e}", "ERROR")


def _start_thread(job: Job, steps: list[tuple[str, Callable[[], dict | None]]]):
    t = threading.Thread(target=_run_steps, args=(job, steps), daemon=True)
    t.start()

# -----------------------------------------------------------------------------------
# "Mocks" de Sankhya — aqui é onde você troca por chamadas reais depois
def step_auth():
    time.sleep(1.0)
    return {"token": "mock-sankhya-token"}

def step_clientes():
    time.sleep(1.0 + random.random())
    return {"clientes_atualizados": random.randint(5, 40)}

def step_produtos():
    time.sleep(1.0 + random.random())
    return {"produtos_atualizados": random.randint(20, 90)}

def step_tabelas():
    time.sleep(1.0 + random.random())
    return {"tabelas_precos": random.randint(1, 5)}

def step_pedidos():
    time.sleep(1.0 + random.random())
    return {"pedidos_importados": random.randint(2, 15)}

def build_steps(job_type: str):
    if job_type == "sankhya_demo":
        return [
            ("Autenticação no Sankhya", step_auth),
            ("Sincronizar clientes",     step_clientes),
            ("Sincronizar produtos",     step_produtos),
            ("Sincronizar tabelas",      step_tabelas),
            ("Importar pedidos",         step_pedidos),
        ]
    elif job_type == "full_load_demo":
        return [
            ("Full load — clientes", step_clientes),
            ("Full load — produtos", step_produtos),
            ("Full load — pedidos",  step_pedidos),
        ]
    else:
        return [("Passo único", lambda: {"echo": job_type})]

# -----------------------------------------------------------------------------------
# API Views

class JobsRunView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        body: { "type": "sankhya_demo" | "full_load_demo", "name": "opcional", "payload": {...} }
        """
        body = request.data or {}
        job_type = (body.get("type") or "sankhya_demo").strip()
        name = body.get("name") or (f"Job {job_type}")
        payload = body.get("payload") or {}

        with transaction.atomic():
            job = Job.objects.create(name=name, type=job_type, payload=payload)
            _log(job, "Criado e enfileirado")
        steps = build_steps(job_type)
        _start_thread(job, steps)
        return Response({"id": str(job.id), "status": job.status}, status=http_status.HTTP_201_CREATED)


class JobsListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Job.objects.all()
        page = int(request.query_params.get("page") or 1)
        p = Paginator(qs, 20)
        pg = p.get_page(page)
        data = [
            {
                "id": str(j.id),
                "name": j.name,
                "type": j.type,
                "status": j.status,
                "progress": j.progress,
                "created_at": j.created_at.isoformat(),
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in pg.object_list
        ]
        return Response({"results": data, "page": page, "pages": p.num_pages})


class JobDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, job_id):
        try:
            j = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"detail": "not found"}, status=404)
        return Response({
            "id": str(j.id),
            "name": j.name,
            "type": j.type,
            "status": j.status,
            "progress": j.progress,
            "payload": j.payload,
            "result": j.result,
            "created_at": j.created_at.isoformat(),
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        })


class JobLogsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, job_id):
        try:
            j = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"detail": "not found"}, status=404)

        page = int(request.query_params.get("page") or 1)
        p = Paginator(j.logs.all(), 50)
        pg = p.get_page(page)
        data = [
            {
                "ts": l.ts.isoformat(),
                "level": l.level,
                "message": l.message,
            } for l in pg.object_list
        ]
        return Response({"results": data, "page": page, "pages": p.num_pages})
