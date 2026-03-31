from rest_framework import serializers
from .models import Country, Genre, AgeRating, Director, Movie, Series


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'iso_code']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'description']


class AgeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeRating
        fields = ['id', 'title']  


class DirectorSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Director
        fields = ['id', 'name', 'birth_date', 'country']


class MovieSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(read_only=True)
    director = DirectorSerializer(read_only=True)
    age_rating = AgeRatingSerializer(read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'synopsis', 'year', 'release_date',
            'duration_minutes', 'rating', 'genre', 'director', 'age_rating',
        ]


class SeriesSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(read_only=True)
    director = DirectorSerializer(read_only=True)

    class Meta:
        model = Series
        fields = ['id', 'title', 'synopsis', 'start_year', 'end_year',
                  'total_seasons', 'rating', 'genre', 'director']