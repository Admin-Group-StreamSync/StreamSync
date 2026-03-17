from django.shortcuts import render, redirect

def home(request):
    return render(request, "pages/home.html")
def vista_nueva_cuenta(request):
    return render(request, 'registration/login.html')
def pagina_perfil1(request):
    return render(request, 'registration/pagina_perfil1.html')
def perfil_principal(request):
    return render(request, 'registration/pagina_perfil1.html')
def sign_in2(request):
    return render(request, 'registration/sign_in2.html')
def pagina_principal(request):
    return render(request, 'pages/pagina_principal.html')
def profile2(request):
    return render(request, 'profile2.html')
def llistes(request):
    return render(request, 'llistes.html')
def login(request):
    if request.method == "POST":
        return redirect('pagina_principal')
    return render(request, 'base.html')

