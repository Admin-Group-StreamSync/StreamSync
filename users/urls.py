from django.urls import path
from . import views

urlpatterns = [
    # PÀGINA PRINCIPAL
    path('', views.pagina_principal, name='pagina_principal'),

    # REGISTRE I GESTIÓ D'USUARIS
    path('registre/', views.crear_cuenta, name='registre'),
    path('perfil/', views.pagina_perfil1, name='pagina_perfil1'),
    path('perfil/preferencies/', views.profile2, name='profile2'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    path('esborrar-compte/', views.esborrar_compte, name='esborrar_compte'),

    # CERCA INTEL·LIGENT
    path('cerca/', views.cerca_contingut, name='cerca_contingut'),

    # CATÀLEG
    path('cataleg/', views.catalogo, name='catalogo'),
    path('cataleg/peliculas/', views.catalogo, {'tipus': 'movie'}, name='cataleg_pelis'),
    path('cataleg/series/', views.catalogo, {'tipus': 'series'}, name='cataleg_series'),

    # DETALL DEL CONTINGUT (Actualitzat amb <str:tipus>)
    path('cataleg/detall/<str:tipus>/<str:content_id>/', views.detall_contingut, name='pagina_contingut'),

    # RESSENYES (Actualitzat per mantenir la coherència amb el detall)
    path('cataleg/detall/<str:tipus>/<str:content_id>/opinar/', views.publicar_ressenya, name='publicar_ressenya'),
    path('ressenya/eliminar/<int:ressenya_id>/', views.eliminar_ressenya, name='eliminar_ressenya'),

    # GESTIÓ DE LLISTES I CARPETES
    path('llistes/', views.llistes, name='llistes'),
    path('llistes/crear/', views.crear_llista, name='crear_llista'),
    path('llistes/eliminar/<int:carpeta_id>/', views.eliminar_carpeta, name='eliminar_carpeta'),

    # AFEGIR/TREURE (També recomano passar el tipus si la vista ho requereix per a la DB local)
    path('llistes/afegir/<str:tipus>/<str:content_id>/', views.afegir_a_llista, name='afegir_a_llista'),
    path('llistes/treure/<str:tipus>/<str:content_id>/', views.treure_de_llista, name='treure_de_llista'),

    path('llistes/carpeta/<int:carpeta_id>/', views.detall_carpeta, name='detall_carpeta'),
    path('llistes/editar/<int:carpeta_id>/', views.editar_llista, name='editar_llista'),


    # STATISTICS DATA MANAGEMENT (Always use POST for those)
    path("statistics/views", views.register_view ,name="register_view"), ##
]