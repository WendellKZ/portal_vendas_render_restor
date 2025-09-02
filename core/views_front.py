from django.shortcuts import render, redirect

def dashboard_view(request):
    # Se quiser, injete flags (ex.: checar cookie 'jwt') para mostrar "logado"
    return render(request, 'dashboard.html', {})

def itens_view(request):
    return render(request, 'relatorios_itens.html', {})

def resumo_view(request):
    return render(request, 'relatorios_resumo.html', {})

def jobs_page(request):
    return render(request, "jobs.html")

def logout_view(request):
    resp = redirect('portal:dashboard')
    # Apaga cookies/sessões do JWT se estiver usando cookie
    resp.delete_cookie('jwt')
    resp.delete_cookie('access')
    return resp

