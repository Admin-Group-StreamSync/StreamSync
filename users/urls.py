from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_principal, name='pagina_principal'), # La home real
    path('registre/', views.crear_cuenta, name='crear_cuenta'),
    path('preferencies/', views.preferencias_registro, name='sign_in2'),
    path('perfil/', views.pagina_perfil1, name='pagina_perfil1'),
    path('perfil/preferencies/', views.profile2, name='profile2'),
    path('llistes/', views.llistes, name='llistes'),
    path('esborrar-compte/', views.esborrar_compte, name='esborrar_compte'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    path('cataleg/', views.catalogo, name='catalogo'),
    path('contingut/<int:content_id>/', views.detall_contingut, name='detall_contingut'),
]