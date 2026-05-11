from django.urls import path

from apps.users.views import *

urlpatterns = [
    # HOME PAGE
    path('', home_page, name='pagina_principal'),

    # REGISTRATION AND USER MANAGEMENT
    path('registre/', crear_cuenta, name='registre'),
    path('perfil/', profile_page1, name='pagina_perfil1'),
    path('perfil/preferencies/', profile2, name='profile2'),
    path('perfil/password/', cambiar_password, name='cambiar_password'),
    path('esborrar-compte/', delete_account, name='esborrar_compte'),



    # REVIEWS (Updated to keep consistency with detail)
    path('cataleg/detall/<str:tipus>/<str:content_id>/opinar/', publish_review, name='publicar_ressenya'),
    path('ressenya/eliminar/<int:ressenya_id>/', delete_review, name='eliminar_ressenya'),

    # LISTS AND FOLDERS MANAGEMENT
    path('llistes/', lists, name='llistes'),
    path('llistes/crear/', create_list, name='crear_llista'),
    path('llistes/eliminar/<int:carpeta_id>/', delete_folder, name='eliminar_carpeta'),

    # ADD/REMOVE (Passing tipus is recommended if the view needs it for local DB)
    path('llistes/afegir/<str:tipus>/<str:content_id>/', add_to_list, name='afegir_a_llista'),
    path('llistes/treure/<str:tipus>/<str:content_id>/', remove_from_list, name='treure_de_llista'),

    path('llistes/carpeta/<int:carpeta_id>/', folder_detail, name='detall_carpeta'),
    path('llistes/editar/<int:carpeta_id>/', edit_list, name='editar_llista'),


    # STATISTICS DATA MANAGEMENT (Always use POST for those)
    path("statistics/views", register_view, name="register_view"), ##

    # DASHBOARD SPM
    path('dashboard/<str:plataforma_nom>/', dashboard_manager, name='dashboard_manager'),
    # FEEDBACK PAGE
    path('feedback/', feedback_view, name='feedback'),

]
