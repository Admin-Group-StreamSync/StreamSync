from django.urls import path

from apps.lists.views import *

urlpatterns = [

    # LISTS AND FOLDERS MANAGEMENT
    path('llistes/', lists, name='llistes'),
    path('llistes/crear/', create_list, name='crear_llista'),
    path('llistes/eliminar/<int:carpeta_id>/', delete_folder, name='eliminar_carpeta'),

    # ADD/REMOVE — <content_id:> captura punts però NO barres
    path('llistes/afegir/<str:tipus>/<content_id:content_id>/', add_to_list, name='afegir_a_llista'),
    path('llistes/treure/<str:tipus>/<content_id:content_id>/', remove_from_list, name='treure_de_llista'),

    path('llistes/carpeta/<int:carpeta_id>/', folder_detail, name='detall_carpeta'),
    path('llistes/editar/<int:carpeta_id>/', edit_list, name='editar_llista'),

]