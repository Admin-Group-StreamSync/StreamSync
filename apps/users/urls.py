from django.urls import path,include
from apps.users import views

urlpatterns = [
    # HOME PAGE
    path('', views.home_page, name='pagina_principal'),

    # REGISTRATION AND USER MANAGEMENT
    path('registre/', views.crear_cuenta, name='registre'),
    path('perfil/', views.profile_page1, name='pagina_perfil1'),
    path('perfil/avatar/', views.update_avatar, name='update_avatar'),
    path('perfil/preferencies/', views.profile2, name='profile2'),
    path('perfil/password/', views.cambiar_password, name='cambiar_password'),
    path('esborrar-compte/', views.delete_account, name='esborrar_compte'),

    # SMART SEARCH







    # COOKIES AND LEGAL
    path("cookies/", include("cookie_consent.urls")),
    path('legal/terms', views.termsofuse_view, name="legal_terms"),
    path('legal/privacy', views.privacy_view, name="legal_privacy"),
    path('legal/cookies', views.cookies_view, name="legal_cookies"),
    path('legal/content_disclaimer', views.content_disclaimer_view, name="legal_content_disclaimer"),

]
