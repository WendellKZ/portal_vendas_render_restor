
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.views_jobs import JobsRunView, JobsListView, JobDetailView, JobLogsView

from .views_reports import (
    VendasResumoView, ItensMaisVendidosView,
    MTDYTDView, HeatmapUFView,
    SimuladorCalcularView, JobRunDemoView
)

urlpatterns = [
    # Auth
    path('auth/login/',   TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),

    # Relatórios
    path('relatorios/vendas-resumo/',        VendasResumoView.as_view()),
    path('relatorios/itens-mais-vendidos/',  ItensMaisVendidosView.as_view()),
    path('relatorios/mtd-ytd/',              MTDYTDView.as_view()),
    path('relatorios/heatmap-uf/',           HeatmapUFView.as_view()),

    # Util
    path('simulador/calcular/',              SimuladorCalcularView.as_view()),
    path('jobs/run-demo/',                   JobRunDemoView.as_view()),

    path("jobs/run/", JobsRunView.as_view(), name="jobs-run"),
    path("jobs/",      JobsListView.as_view(), name="jobs-list"),
    path("jobs/<uuid:job_id>/", JobDetailView.as_view(), name="jobs-detail"),
    path("jobs/<uuid:job_id>/logs/", JobLogsView.as_view(), name="jobs-logs"),
]

# (Opcional) Mantém endpoints de CNPJ se o módulo existir
try:
    from .views_cnpj import CNPJLookupView, ClienteCriarPorCNPJView
    urlpatterns += [
        path('cnpj/lookup/', CNPJLookupView.as_view()),
        path('clientes/criar-por-cnpj/', ClienteCriarPorCNPJView.as_view()),
    ]
except Exception:
    pass
