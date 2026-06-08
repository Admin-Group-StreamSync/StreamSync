"""
Behave environment configuration for StreamSync BDD tests.
Sets up Django test environment and shared context.
"""
import os
import django
from unittest.mock import patch, MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "StreamSync.settings")


def before_all(context):
    """Set up Django before the test suite runs."""
    django.setup()
    context.PLACEHOLDER = "https://via.placeholder.com/300x450"
    context.MOCK_MOVIES = [
        {
            "id": "8080_1", "titol": "Inception", "sinopsi": "Mind-bending heist",
            "any": 2010, "rating": "8.8", "plataforma": "CinePlus",
            "plataformes_disponibles": ["CinePlus"], "tipus": "movie",
            "genre_id": "1", "director_id": "1", "age_rating_id": "1",
            "genere_nom": "Sci-Fi", "director_nom": "Nolan", "edat_nom": "13+",
            "imatge": "https://via.placeholder.com/300x450"
        }
    ]
    context.MOCK_SERIES = [
        {
            "id": "8081_1", "titol": "Breaking Bad", "sinopsi": "Chemistry teacher goes criminal",
            "any": 2008, "rating": "9.5", "plataforma": "StreamHub",
            "plataformes_disponibles": ["StreamHub"], "tipus": "series",
            "genre_id": "2", "director_id": "2", "age_rating_id": "2",
            "genere_nom": "Drama", "director_nom": "Gilligan", "edat_nom": "18+",
            "imatge": "https://via.placeholder.com/300x450"
        }
    ]
    context.MOCK_GENRES = [{"id": 1, "name": "Sci-Fi"}, {"id": 2, "name": "Drama"}]
    context.MOCK_RATINGS = [{"id": 1, "description": "13+"}, {"id": 2, "description": "18+"}]
    context.MOCK_DIRECTORS = [{"id": 1, "name": "Nolan"}, {"id": 2, "name": "Gilligan"}]


def before_scenario(context, scenario):
    """Set up a fresh client and DB state for every scenario."""
    from django.test import Client
    context.client = Client()
    context.response = None
    context.user = None


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    from django.contrib.auth.models import User
    from apps.contents.models import Pelicula
    from apps.reviews.models import Ressenya
    from apps.lists.models import LlistaPersonal, Carpeta
    from apps.analytics.models import Views

    Views.objects.all().delete()
    Ressenya.objects.all().delete()
    LlistaPersonal.objects.all().delete()
    Carpeta.objects.all().delete()
    Pelicula.objects.all().delete()
    User.objects.all().delete()
