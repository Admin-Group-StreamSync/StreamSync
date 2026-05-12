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


    # FEEDBACK PAGE
    path('feedback/', feedback_view, name='feedback'),

    # COOKIES AND LEGAL
    path('legal/terms', termsofuse_view, name="legal_terms"),
    path('legal/privacy', privacy_view, name="legal_privacy"),
    path('legal/cookies', cookies_view, name="legal_cookies"),
    path('legal/content_disclaimer', content_disclaimer_view, name="legal_content_disclaimer"),

]
