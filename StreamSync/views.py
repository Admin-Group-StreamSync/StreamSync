from django.shortcuts import render

def home(request):
    return render(request, "pages/home.html")

def prove(request):
    print("Hello") # comment