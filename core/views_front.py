# core/views_front.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages


def dashboard_view(request):
    # Renderiza o dashboard; o formulário de login simples fica no template
    return render(request, "dashboard.html")


def itens_view(request):
    return render(request, "itens.html")


def resumo_view(request):
    return render(request, "resumo.html")


@csrf_protect
def simple_login(request):
    """
    Login bem simples usado pelo card no dashboard.
    POST: username + password -> autentica e redireciona para o dashboard.
    GET: apenas redireciona.
    """
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            messages.error(request, "Usuário ou senha inválidos.")
        return redirect("portal:dashboard")
    return redirect("portal:dashboard")


def simple_logout(request):
    logout(request)
    return redirect("portal:dashboard")
