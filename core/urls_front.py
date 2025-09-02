from django.urls import path
from .views_front import dashboard_view, itens_view, resumo_view, logout_view
from django.urls import path
from . import views_front

app_name = "portal"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("itens/", itens_view, name="itens"),
    path("items/", itens_view, name="items_alias"),  # alias em inglês
    path("resumo/", resumo_view, name="resumo"),
    path("sair/", logout_view, name="logout"),
    path("jobs/", views_front.jobs_page, name="jobs"),
]
