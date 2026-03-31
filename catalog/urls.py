from django.urls import path
from . import views

urlpatterns = [
    path('movies/', views.MovieListView.as_view(), name='movie-list'),
    path('series/', views.SeriesListView.as_view(), name='series-list'),
    path('directors/', views.DirectorListView.as_view(), name='director-list'),
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('age-ratings/', views.AgeRatingListView.as_view(), name='age-rating-list'),
]