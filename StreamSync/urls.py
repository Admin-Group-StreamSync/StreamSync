from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),


    path('nova_compta/', views.vista_nueva_cuenta, name='crear_cuenta'),
    path('pagina_perfil1/', views.pagina_perfil1, name='pagina_perfil1'),
    path('pagina_perfil1', views.pagina_perfil1),
    path('pagina_perfil1.html', views.pagina_perfil1),
]
