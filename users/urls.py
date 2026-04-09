from django.urls import path
from . import views

urlpatterns = [
    # Pàgina principal
    path('', views.pagina_principal, name='pagina_principal'),

    # REGISTRE
    path('registre/', views.crear_cuenta, name='registre'),

    # PERFIL I PREFERÈNCIES
    path('perfil/', views.pagina_perfil1, name='pagina_perfil1'),
    path('perfil/preferencies/', views.profile2, name='profile2'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),

    # CATÀLEG
    path('cataleg/', views.catalogo, name='catalogo'),
    path('cataleg/peliculas/', views.catalogo, {'tipus': 'movie'}, name='cataleg_pelis'),
    path('cataleg/series/', views.catalogo, {'tipus': 'series'}, name='cataleg_series'),

    # --- AFEGEIX AQUESTA LÍNIA AQUÍ ---
    path('cataleg/detall/<str:content_id>/', views.detall_contingut, name='detall_contingut'),
    # ----------------------------------

    # ALTRES
    path('llistes/', views.llistes, name='llistes'),
    path('esborrar-compte/', views.esborrar_compte, name='esborrar_compte'),
]