
from django.urls import path
from apps.contents.views import *

urlpatterns = [

    # SMART SEARCH
    path('cerca/', search_content, name='cerca_contingut'),

    # CATALOG
    path('cataleg/', catalogo, name='catalogo'),

    path('cataleg/peliculas/', catalogo, {'tipus': 'movie'}, name='cataleg_pelis'),
    path('cataleg/series/', catalogo, {'tipus': 'series'}, name='cataleg_series'),

    # CONTENT DETAIL (Updated with <str:tipus>)
    path('cataleg/detall/<str:tipus>/<str:content_id>/', content_detail, name='pagina_contingut'),
]
