from django.urls import path
from . import views_front

app_name = "portal"

urlpatterns = [
    path("", views_front.dashboard_view, name="dashboard"),
    path("login/", views_front.login_view, name="login"),
    path("logout/", views_front.logout_view, name="logout"),
    path("itens/", views_front.itens_view, name="itens"),
    path("resumo/", views_front.resumo_view, name="resumo"),
]
