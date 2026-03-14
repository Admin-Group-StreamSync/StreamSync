from django.shortcuts import render

def home(request):
    return render(request, "pages/home.html")
def vista_nueva_cuenta(request):
    return render(request, 'nova_compta.html')
def pagina_perfil1(request):
    return render(request, 'pagina_perfil1.html')
def sign_in2(request):
    return render(request, 'sign_in2.html')
def pagina_principal(request):
    return render(request, 'pagina_principal.html')
def profile2(request):
    return render(request, 'profile2.html')
