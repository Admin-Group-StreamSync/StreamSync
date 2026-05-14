from django.urls import path

from apps.analytics.views import *

urlpatterns = [
# STATISTICS DATA MANAGEMENT (Always use POST for those)
    path("statistics/views", register_view, name="register_view"), ##

    # DASHBOARD SPM
    path('dashboard/<str:plataforma_nom>/', dashboard_manager, name='dashboard_manager'),
]