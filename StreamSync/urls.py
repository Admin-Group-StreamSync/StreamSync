from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),


    path('nova_compta/', views.vista_nueva_cuenta, name='crear_cuenta'),
    path('login/', views.login, name='login'),
    path('sign_in2/', views.sign_in2, name='sign_in2'),
    path('pagina_perfil1/', views.pagina_perfil1, name='pagina_perfil1'),
    path('pagina_perfil1', views.pagina_perfil1),
    path('pagina_perfil1.html', views.pagina_perfil1),
    path('perfil_principal/', views.perfil_principal, name='perfil_principal'),
    path('pagina_principal/', views.pagina_principal, name='pagina_principal'),
    path('pagina_principal', views.pagina_principal),
    path('pagina_principal.html', views.pagina_principal),
    path('profile2/', views.profile2, name='profile2'),
    path('profile2', views.profile2),
    path('profile2.html', views.profile2),
]
