"""
Step definitions for lists_and_reviews.feature
"""
from unittest.mock import patch

from behave import given, when, then
from django.contrib.auth.models import User
from django.urls import reverse

from apps.contents.models import Pelicula
from apps.lists.models import Carpeta, LlistaPersonal
from apps.reviews.models import Ressenya

_MOVIES = "apps.contents.views.get_all_movies"
_SERIES = "apps.contents.views.get_all_series"
_GENRES = "apps.contents.views.get_genres_from_api"
_RATINGS = "apps.contents.views.get_age_ratings_from_api"
_DIRECTORS = "apps.contents.views.get_directors_from_api"
_TMDB = "apps.contents.views.get_tmdb_image"
_ENRICH = "apps.contents.views.enrich_tmdb_images"
PLACEHOLDER = "https://via.placeholder.com/300x450"


def _get_current_user(context):
    """Retrieve the user linked to current session."""
    if context.user:
        return context.user
    # Try via session
    from django.contrib.auth.models import User as U
    users = U.objects.filter(username__in=["lr_user"])
    if users.exists():
        return users.first()
    return None


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------

@given('I have a folder named "{name}"')
def step_create_folder(context, name):
    user = User.objects.filter(username="lr_user").first()
    context.folder = Carpeta.objects.create(usuari=user, nom=name)


@given('movie "{pk}" is in my personal list')
def step_movie_in_list(context, pk):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    LlistaPersonal.objects.get_or_create(usuari=user, pelicula=movie)


@given('I have already reviewed movie "{pk}" with score {score:d}')
def step_already_reviewed(context, pk, score):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    Ressenya.objects.update_or_create(
        usuari=user, pelicula=movie,
        defaults={"puntuacio": score}
    )


# ---------------------------------------------------------------------------
# When — lists
# ---------------------------------------------------------------------------

@when('I add movie "{pk}" to my list with folder')
def step_add_to_list(context, pk):
    folder_id = context.folder.id if hasattr(context, "folder") else ""
    url = reverse("afegir_a_llista", kwargs={"tipus": "movie", "content_id": pk})
    with patch(_MOVIES, return_value=context.MOCK_MOVIES), \
         patch(_SERIES, return_value=context.MOCK_SERIES), \
         patch(_GENRES, return_value=context.MOCK_GENRES), \
         patch(_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS), \
         patch(_TMDB, return_value=PLACEHOLDER), \
         patch(_ENRICH, return_value=[]):
        context.response = context.client.post(url, {"carpeta_id": folder_id})


@when('I try to add movie "{pk}" to my list')
def step_try_add_to_list_anon(context, pk):
    url = reverse("afegir_a_llista", kwargs={"tipus": "movie", "content_id": pk})
    context.response = context.client.post(url, {})


@when('I remove movie "{pk}" from my list')
def step_remove_from_list(context, pk):
    url = reverse("treure_de_llista", kwargs={"tipus": "movie", "content_id": pk})
    context.response = context.client.post(url)


@when("I visit the lists page")
def step_visit_lists(context):
    context.response = context.client.get(reverse("llistes"))


# ---------------------------------------------------------------------------
# When — reviews
# ---------------------------------------------------------------------------

@when('I post a review for movie "{pk}" with score {score:d} and comment "{comment}"')
def step_post_review(context, pk, score, comment):
    url = reverse("publicar_ressenya", kwargs={"tipus": "movie", "content_id": pk})
    context.response = context.client.post(url, {
        "puntuacio": score,
        "comentari": comment,
    })


# ---------------------------------------------------------------------------
# Then — lists
# ---------------------------------------------------------------------------

@then('movie "{pk}" is in my list')
def step_movie_in_my_list(context, pk):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    assert LlistaPersonal.objects.filter(usuari=user, pelicula=movie).exists(), \
        f"Movie {pk} was not found in user's list"


@then('there is only 1 item for movie "{pk}" in my list')
def step_one_item_for_movie(context, pk):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    count = LlistaPersonal.objects.filter(usuari=user, pelicula=movie).count()
    assert count == 1, f"Expected 1 list item, got {count}"


@then('movie "{pk}" is not in my list')
def step_movie_not_in_list(context, pk):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    assert not LlistaPersonal.objects.filter(usuari=user, pelicula=movie).exists(), \
        f"Movie {pk} was unexpectedly found in user's list"


# ---------------------------------------------------------------------------
# Then — reviews
# ---------------------------------------------------------------------------

@then('a review exists for movie "{pk}" with score {score:d}')
def step_review_exists(context, pk, score):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    r = Ressenya.objects.filter(usuari=user, pelicula=movie).first()
    assert r is not None, f"No review found for movie {pk}"
    assert r.puntuacio == score, f"Expected score {score}, got {r.puntuacio}"


@then('there is only 1 review for movie "{pk}"')
def step_one_review(context, pk):
    user = User.objects.filter(username="lr_user").first()
    movie = Pelicula.objects.get(id=pk)
    count = Ressenya.objects.filter(usuari=user, pelicula=movie).count()
    assert count == 1, f"Expected 1 review, got {count}"
