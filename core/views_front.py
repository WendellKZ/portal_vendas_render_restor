from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

def dashboard_view(request):
    # Mostra o login apenas se não estiver autenticado
    return render(request, "dashboard.html", {})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username") or ""
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("portal:dashboard")
        messages.error(request, "Usuário ou senha inválidos.")
    # Volta ao dashboard (onde o formulário aparece quando não autenticado)
    return redirect("portal:dashboard")

def logout_view(request):
    logout(request)
    return redirect("portal:dashboard")

@login_required(login_url="/app/")
def itens_view(request):
    return render(request, "itens.html", {})

@login_required(login_url="/app/")
def resumo_view(request):
    return render(request, "resumo.html", {})
