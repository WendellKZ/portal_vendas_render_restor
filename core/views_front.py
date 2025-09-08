from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

# DASHBOARD (público; mostra login se não autenticado)
def dashboard_view(request):
    return render(request, "dashboard.html", {})

# LOGIN (processa POST do formulário inline)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username") or ""
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("portal:dashboard")
        messages.error(request, "Usuário ou senha inválidos.")
    return redirect("portal:dashboard")

# LOGOUT
def logout_view(request):
    logout(request)
    return redirect("portal:dashboard")

# Páginas internas (exigem login)
@login_required(login_url="/app/")
def itens_view(request):
    return render(request, "itens.html", {})

@login_required(login_url="/app/")
def resumo_view(request):
    return render(request, "resumo.html", {})
