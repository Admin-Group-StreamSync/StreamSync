# StreamSync/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.users.views import StreamSyncLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')),
    path('', include('apps.contents.urls')),
    path('', include('apps.analytics.urls')),
    path('', include('apps.lists.urls')),

    path('login/', StreamSyncLoginView.as_view(template_name='registration/login.html'), name='login'),

    # LOGOUT
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path("cookies/", include("cookie_consent.urls")),

]
