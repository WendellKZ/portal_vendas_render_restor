from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def dashboard_view(request):
    return render(request, "dashboard.html")

def login_view(request):
    if request.method == "POST":
        user = authenticate(request,
                            username=request.POST.get("username"),
                            password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect("portal:dashboard")
        messages.error(request, "Usuário ou senha inválidos.")
    return redirect("portal:dashboard")

def logout_view(request):
    logout(request)
    return redirect("portal:dashboard")

@login_required(login_url="/app/")
def itens_view(request):
    return render(request, "itens.html")

@login_required(login_url="/app/")
def resumo_view(request):
    return render(request, "resumo.html")
