from django.urls import path

from apps.contents.views import *

urlpatterns = [

    path('cerca/', search_content, name='cerca_contingut'),

    # CATALOG
    path('cataleg/', catalogo, name='catalogo'),
    path('cataleg/peliculas/', catalogo, {'tipus': 'movie'}, name='cataleg_pelis'),
    path('cataleg/series/', catalogo, {'tipus': 'series'}, name='cataleg_series'),

    # CONTENT DETAIL — <path:content_id> needed because IDs contain dots (e.g. movies-api-1-b2np.onrender.com_1)
    path('cataleg/detall/<str:tipus>/<path:content_id>/', content_detail, name='pagina_contingut'),
]