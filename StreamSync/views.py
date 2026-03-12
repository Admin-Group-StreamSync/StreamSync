from django.shortcuts import render

def home(request):
    return render(request, "pages/home.html")
def vista_nueva_cuenta(request):
    return render(request, 'nova_compta.html')