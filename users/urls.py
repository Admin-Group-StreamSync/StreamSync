from django.urls import include, path

from users import views

urlpatterns = [
    path('users/', views.users, name='users'),
]