from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),  # Si tienes una app 'users'

    # Esta es la ruta para crear la cuenta
    path('nova_compta/', views.vista_nueva_cuenta, name='crear_cuenta'),
]