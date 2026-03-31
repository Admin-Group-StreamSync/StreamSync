from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Movie, Series, Director, Genre, AgeRating
from .serializers import (
    MovieSerializer, SeriesSerializer,
    DirectorSerializer, GenreSerializer, AgeRatingSerializer,
)
from .authentication import ApiKeyAuthentication


class MovieListView(APIView):
    """
    GET /movies/
    Filtros: genre, director, age_rating, id, title, synopsis
    """
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        queryset = Movie.objects.select_related(
            'genre', 'director', 'director__country', 'age_rating'
        ).all()

        # Filtros del swagger
        if genre := request.query_params.get('genre'):
            queryset = queryset.filter(genre__name__icontains=genre)
        if director := request.query_params.get('director'):
            queryset = queryset.filter(director__name__icontains=director)
        if age_rating := request.query_params.get('age_rating'):
            queryset = queryset.filter(age_rating__description__icontains=age_rating)
        if movie_id := request.query_params.get('id'):
            queryset = queryset.filter(id=movie_id)
        if title := request.query_params.get('title'):
            queryset = queryset.filter(title__icontains=title)
        if synopsis := request.query_params.get('synopsis'):
            queryset = queryset.filter(synopsis__icontains=synopsis)

        serializer = MovieSerializer(queryset, many=True)
        return Response(serializer.data)


class SeriesListView(APIView):
    """
    GET /series/
    Filtros: genre, director
    """
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        queryset = Series.objects.select_related(
            'genre', 'director', 'director__country'
        ).all()

        if genre := request.query_params.get('genre'):
            queryset = queryset.filter(genre__name__icontains=genre)
        if director := request.query_params.get('director'):
            queryset = queryset.filter(director__name__icontains=director)

        serializer = SeriesSerializer(queryset, many=True)
        return Response(serializer.data)


class DirectorListView(APIView):
    """GET /directors/"""
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        directors = Director.objects.select_related('country').all()
        serializer = DirectorSerializer(directors, many=True)
        return Response(serializer.data)


class GenreListView(APIView):
    """GET /genres/"""
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)


class AgeRatingListView(APIView):
    """GET /age-ratings/"""
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        ratings = AgeRating.objects.all()
        serializer = AgeRatingSerializer(ratings, many=True)
        return Response(serializer.data)