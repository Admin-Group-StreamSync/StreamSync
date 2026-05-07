from django.urls import path
from . import views

urlpatterns = [
    # HOME PAGE
    path('', views.home_page, name='pagina_principal'),

    # REGISTRATION AND USER MANAGEMENT
    path('registre/', views.crear_cuenta, name='registre'),
    path('perfil/', views.profile_page1, name='pagina_perfil1'),
    path('perfil/preferencies/', views.profile2, name='profile2'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    path('esborrar-compte/', views.delete_account, name='esborrar_compte'),

    # SMART SEARCH
    path('cerca/', views.search_content, name='cerca_contingut'),

    # CATALOG
    path('cataleg/', views.catalogo, name='catalogo'),
    path('cataleg/peliculas/', views.catalogo, {'tipus': 'movie'}, name='cataleg_pelis'),
    path('cataleg/series/', views.catalogo, {'tipus': 'series'}, name='cataleg_series'),

    # CONTENT DETAIL (Updated with <str:tipus>)
    path('cataleg/detall/<str:tipus>/<str:content_id>/', views.content_detail, name='pagina_contingut'),

    # REVIEWS (Updated to keep consistency with detail)
    path('cataleg/detall/<str:tipus>/<str:content_id>/opinar/', views.publish_review, name='publicar_ressenya'),
    path('ressenya/eliminar/<int:ressenya_id>/', views.delete_review, name='eliminar_ressenya'),

    # LISTS AND FOLDERS MANAGEMENT
    path('llistes/', views.lists, name='llistes'),
    path('llistes/crear/', views.create_list, name='crear_llista'),
    path('llistes/eliminar/<int:carpeta_id>/', views.delete_folder, name='eliminar_carpeta'),

    # ADD/REMOVE (Passing tipus is recommended if the view needs it for local DB)
    path('llistes/afegir/<str:tipus>/<str:content_id>/', views.add_to_list, name='afegir_a_llista'),
    path('llistes/treure/<str:tipus>/<str:content_id>/', views.remove_from_list, name='treure_de_llista'),

    path('llistes/carpeta/<int:carpeta_id>/', views.folder_detail, name='detall_carpeta'),
    path('llistes/editar/<int:carpeta_id>/', views.edit_list, name='editar_llista'),


    # STATISTICS DATA MANAGEMENT (Always use POST for those)
    path("statistics/views", views.register_view ,name="register_view"), ##

    # FEEDBACK PAGE
    path('feedback/', views.feedback_view, name='feedback'),

]
