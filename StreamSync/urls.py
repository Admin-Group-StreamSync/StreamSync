# StreamSync/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),  # Les teves rutes d'usuari

    # LOGIN: Utilitzem la vista de Django però el TEU template
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('portal-responsables/', auth_views.LoginView.as_view(template_name='registration/login_spm.html'),
         name='login_spm'),

    # LOGOUT
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
