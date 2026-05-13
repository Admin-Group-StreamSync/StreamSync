from django.urls import path

from apps.reviews.views import *

urlpatterns = [
# REVIEWS (Updated to keep consistency with detail)
    path('cataleg/detall/<str:tipus>/<str:content_id>/opinar/', publish_review, name='publicar_ressenya'),
    path('ressenya/eliminar/<int:ressenya_id>/', delete_review, name='eliminar_ressenya'),
    path('feedback/', feedback_view, name='feedback'),

]