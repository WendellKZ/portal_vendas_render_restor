# core/urls_front.py
from django.urls import path
from . import views_front

app_name = "portal"

urlpatterns = [
    path("", views_front.dashboard_view, name="dashboard"),
    path("itens/", views_front.itens_view, name="itens"),
    path("resumo/", views_front.resumo_view, name="resumo"),
    path("login/", views_front.simple_login, name="login"),
    path("logout/", views_front.simple_logout, name="logout"),
]

