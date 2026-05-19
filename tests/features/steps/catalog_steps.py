"""
Step definitions for catalog.feature
"""
from unittest.mock import patch

from behave import given, when, then
from django.urls import reverse

from apps.contents.models import Pelicula

_MOVIES = "apps.contents.views.get_all_movies"
_SERIES = "apps.contents.views.get_all_series"
_GENRES = "apps.contents.views.get_genres_from_api"
_RATINGS = "apps.contents.views.get_age_ratings_from_api"
_DIRECTORS = "apps.contents.views.get_directors_from_api"
_TMDB = "apps.contents.views.get_tmdb_image"
_ENRICH = "apps.contents.views.enrich_tmdb_images"
_SEARCH_GENRES = "apps.contents.views.get_genres_from_api"
_SEARCH_RATINGS = "apps.contents.views.get_age_ratings_from_api"
PLACEHOLDER = "https://via.placeholder.com/300x450"


def _catalog_patches(context):
    return (
        patch(_MOVIES, return_value=context.MOCK_MOVIES),
        patch(_SERIES, return_value=context.MOCK_SERIES),
        patch(_GENRES, return_value=context.MOCK_GENRES),
        patch(_RATINGS, return_value=context.MOCK_RATINGS),
        patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS),
        patch(_ENRICH, side_effect=lambda x: x),
    )


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------

@given('a movie "{pk}" titled "{title}" exists in the database')
def step_movie_in_db(context, pk, title):
    Pelicula.objects.get_or_create(
        id=pk,
        defaults={"titol": title, "tipus": "movie", "valoracio": 8.0}
    )


# ---------------------------------------------------------------------------
# When — catalog
# ---------------------------------------------------------------------------

@when("I visit the catalog with mocked API")
def step_visit_catalog(context):
    patches = _catalog_patches(context)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        context.response = context.client.get(reverse("catalogo"))


@when("I visit the movies catalog with mocked API")
def step_visit_movies_catalog(context):
    with patch(_MOVIES, return_value=context.MOCK_MOVIES), \
         patch(_GENRES, return_value=context.MOCK_GENRES), \
         patch(_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS), \
         patch(_ENRICH, side_effect=lambda x: x):
        context.response = context.client.get(reverse("cataleg_pelis"))


@when("I visit the series catalog with mocked API")
def step_visit_series_catalog(context):
    with patch(_SERIES, return_value=context.MOCK_SERIES), \
         patch(_GENRES, return_value=context.MOCK_GENRES), \
         patch(_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS), \
         patch(_ENRICH, side_effect=lambda x: x):
        context.response = context.client.get(reverse("cataleg_series"))


@when("I visit the catalog with 30 mock items")
def step_visit_catalog_30_items(context):
    many_movies = context.MOCK_MOVIES * 30
    # Give unique IDs to avoid deduplication
    for i, m in enumerate(many_movies):
        m = dict(m)
        m["id"] = f"8080_{i}"
        m["titol"] = f"Film {i}"
        many_movies[i] = m

    with patch(_MOVIES, return_value=many_movies), \
         patch(_SERIES, return_value=[]), \
         patch(_GENRES, return_value=context.MOCK_GENRES), \
         patch(_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS), \
         patch(_ENRICH, side_effect=lambda x: x):
        context.response = context.client.get(reverse("catalogo"))


@when('I visit the catalog filtered by platform "{platform}"')
def step_catalog_filter_platform(context, platform):
    patches = _catalog_patches(context)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        context.response = context.client.get(
            reverse("catalogo") + f"?plataforma={platform}"
        )


@when('I visit the catalog filtered by genre "{genre_id}"')
def step_catalog_filter_genre(context, genre_id):
    patches = _catalog_patches(context)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        context.response = context.client.get(
            reverse("catalogo") + f"?genere={genre_id}"
        )


@when('I visit the catalog filtered by director "{director}"')
def step_catalog_filter_director(context, director):
    patches = _catalog_patches(context)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        context.response = context.client.get(
            reverse("catalogo") + f"?director={director}"
        )


@when('I visit the catalog filtered by rating "{rating}"')
def step_catalog_filter_rating(context, rating):
    patches = _catalog_patches(context)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        context.response = context.client.get(
            reverse("catalogo") + f"?valoracio={rating}"
        )


@when('I visit the detail page for movie "{content_id}"')
def step_visit_detail_movie(context, content_id):
    with patch(_MOVIES, return_value=context.MOCK_MOVIES), \
         patch(_SERIES, return_value=context.MOCK_SERIES), \
         patch(_GENRES, return_value=context.MOCK_GENRES), \
         patch(_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_DIRECTORS, return_value=context.MOCK_DIRECTORS), \
         patch(_TMDB, return_value=PLACEHOLDER), \
         patch(_ENRICH, return_value=context.MOCK_MOVIES[:1]):
        context.response = context.client.get(
            reverse("pagina_contingut", kwargs={"tipus": "movie", "content_id": content_id})
        )


@when('I visit the detail page for unknown movie "{content_id}"')
def step_visit_detail_unknown(context, content_id):
    with patch(_MOVIES, return_value=[]), \
         patch(_SERIES, return_value=[]), \
         patch(_GENRES, return_value=[]), \
         patch(_RATINGS, return_value=[]), \
         patch(_DIRECTORS, return_value=[]), \
         patch(_TMDB, return_value=PLACEHOLDER), \
         patch(_ENRICH, return_value=[]):
        context.response = context.client.get(
            reverse("pagina_contingut", kwargs={"tipus": "movie", "content_id": content_id})
        )


# ---------------------------------------------------------------------------
# When — search
# ---------------------------------------------------------------------------

@when('I search for "{query}"')
@when('I search for ""')
def step_search(context, query=""):
    with patch(_MOVIES, return_value=context.MOCK_MOVIES), \
         patch(_SERIES, return_value=context.MOCK_SERIES), \
         patch(_SEARCH_GENRES, return_value=context.MOCK_GENRES), \
         patch(_SEARCH_RATINGS, return_value=context.MOCK_RATINGS), \
         patch(_TMDB, return_value=PLACEHOLDER), \
         patch(_ENRICH, side_effect=lambda x: x):
        context.response = context.client.get(
            reverse("cerca_contingut") + f"?q={query}"
        )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then("the page contains at most 12 items")
def step_at_most_12(context):
    page_obj = context.response.context["page_obj"]
    count = len(page_obj.object_list)
    assert count <= 12, f"Expected ≤12 items per page, got {count}"


@then('the search result title is "{title}"')
def step_search_result_title(context, title):
    result = context.response.context.get("resultat")
    assert result is not None, "No search result found"
    assert result["titol"] == title, \
        f"Expected title '{title}', got '{result['titol']}'"


@then("a search result is found")
def step_search_result_found(context):
    result = context.response.context.get("resultat")
    assert result is not None, "Expected a search result but got None"


@then("no search result is found")
def step_no_search_result(context):
    result = context.response.context.get("resultat")
    assert result is None, f"Expected no result but got: {result}"
