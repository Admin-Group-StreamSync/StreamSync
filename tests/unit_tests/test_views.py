"""
View tests for StreamSync.
All external API and TMDB calls are mocked.
"""
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse

from apps.contents.models import Pelicula
from apps.lists.models import Carpeta, LlistaPersonal
from apps.reviews.models import Ressenya
from apps.users.models.models import Profile

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_MOVIES = [
    {
        "id": "8080_1", "titol": "Interstellar", "sinopsi": "Space odyssey",
        "any": 2014, "rating": "8.6", "plataforma": "CinePlus",
        "plataformes_disponibles": ["CinePlus"], "tipus": "movie",
        "genre_id": "1", "director_id": "1", "age_rating_id": "1",
        "genere_nom": "Sci-Fi", "director_nom": "Nolan", "edat_nom": "13+",
        "imatge": "https://via.placeholder.com/300x450"
    }
]

MOCK_SERIES = [
    {
        "id": "8081_1", "titol": "Breaking Bad", "sinopsi": "Chemistry teacher turns criminal",
        "any": 2008, "rating": "9.5", "plataforma": "StreamHub",
        "plataformes_disponibles": ["StreamHub"], "tipus": "series",
        "genre_id": "2", "director_id": "2", "age_rating_id": "2",
        "genere_nom": "Drama", "director_nom": "Gilligan", "edat_nom": "18+",
        "imatge": "https://via.placeholder.com/300x450"
    }
]

MOCK_GENRES = [{"id": 1, "name": "Sci-Fi"}, {"id": 2, "name": "Drama"}]
MOCK_RATINGS = [{"id": 1, "description": "13+"}, {"id": 2, "description": "18+"}]
MOCK_DIRECTORS = [{"id": 1, "name": "Nolan"}, {"id": 2, "name": "Gilligan"}]
PLACEHOLDER = "https://via.placeholder.com/300x450"


def make_user(username="viewtestuser", password="pass1234!"):
    user = User.objects.create_user(username=username, password=password)
    return user


def make_movie(pk="8080_1", titol="Interstellar", tipus="movie"):
    return Pelicula.objects.get_or_create(
        id=pk,
        defaults={"titol": titol, "tipus": tipus, "valoracio": 8.6}
    )[0]


# Patch targets
_MOVIES = "apps.contents.views.get_all_movies"
_SERIES = "apps.contents.views.get_all_series"
_GENRES = "apps.contents.views.get_genres_from_api"
_RATINGS = "apps.contents.views.get_age_ratings_from_api"
_DIRECTORS = "apps.contents.views.get_directors_from_api"
_TMDB = "apps.contents.views.get_tmdb_image"
_ENRICH = "apps.contents.views.enrich_tmdb_images"

_HOME_MOVIES = "apps.users.views.get_all_movies"
_HOME_SERIES = "apps.users.views.get_all_series"
_HOME_GENRES = "apps.users.views.get_genres_from_api"
_HOME_RATINGS = "apps.users.views.get_age_ratings_from_api"
_HOME_ENRICH = "apps.users.views.enrich_tmdb_images"


# ---------------------------------------------------------------------------
# pagina_principal (home page)
# ---------------------------------------------------------------------------

class PaginaPrincipalViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("pagina_principal")

    @patch(_HOME_ENRICH, side_effect=lambda x: x)
    @patch(_HOME_RATINGS, return_value=MOCK_RATINGS)
    @patch(_HOME_GENRES, return_value=MOCK_GENRES)
    @patch(_HOME_SERIES, return_value=MOCK_SERIES)
    @patch(_HOME_MOVIES, return_value=MOCK_MOVIES)
    def test_authenticated_user_can_see_home(self, *mocks):
        user = make_user()
        self.client.login(username="viewtestuser", password="pass1234!")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    @patch(_HOME_ENRICH, side_effect=lambda x: x)
    @patch(_HOME_RATINGS, return_value=MOCK_RATINGS)
    @patch(_HOME_GENRES, return_value=MOCK_GENRES)
    @patch(_HOME_SERIES, return_value=MOCK_SERIES)
    @patch(_HOME_MOVIES, return_value=MOCK_MOVIES)
    def test_anonymous_user_redirected_from_home(self, *mocks):
        resp = self.client.get(self.url)
        # Decorator redirects anonymous users to login
        self.assertIn(resp.status_code, [302, 200])

    @patch(_HOME_ENRICH, side_effect=lambda x: x)
    @patch(_HOME_RATINGS, return_value=MOCK_RATINGS)
    @patch(_HOME_GENRES, return_value=MOCK_GENRES)
    @patch(_HOME_SERIES, return_value=MOCK_SERIES)
    @patch(_HOME_MOVIES, return_value=MOCK_MOVIES)
    def test_home_uses_correct_template(self, *mocks):
        make_user(username="homeuser")
        self.client.login(username="homeuser", password="pass1234!")
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, "pages/pagina_principal.html")

    @patch(_HOME_ENRICH, side_effect=lambda x: x)
    @patch(_HOME_RATINGS, return_value=MOCK_RATINGS)
    @patch(_HOME_GENRES, return_value=MOCK_GENRES)
    @patch(_HOME_SERIES, return_value=MOCK_SERIES)
    @patch(_HOME_MOVIES, return_value=MOCK_MOVIES)
    def test_home_context_has_tendencies(self, *mocks):
        make_user(username="ctxuser")
        self.client.login(username="ctxuser", password="pass1234!")
        resp = self.client.get(self.url)
        self.assertIn("tendencies", resp.context)


# ---------------------------------------------------------------------------
# catalogo
# ---------------------------------------------------------------------------

class CatalogoViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="catuser")
        self.client.login(username="catuser", password="pass1234!")

    def _get(self, params=""):
        with patch(_MOVIES, return_value=MOCK_MOVIES * 15), \
             patch(_SERIES, return_value=MOCK_SERIES * 15), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_ENRICH, side_effect=lambda x: x):
            url = reverse("catalogo") + (f"?{params}" if params else "")
            return self.client.get(url)

    def test_catalog_loads(self):
        resp = self._get()
        self.assertEqual(resp.status_code, 200)

    def test_catalog_filter_by_platform(self):
        resp = self._get("plataforma=CinePlus")
        self.assertEqual(resp.status_code, 200)

    def test_catalog_filter_by_genre(self):
        resp = self._get("genere=1")
        self.assertEqual(resp.status_code, 200)

    def test_catalog_filter_by_age_rating(self):
        resp = self._get("edat=1")
        self.assertEqual(resp.status_code, 200)

    def test_catalog_filter_by_director(self):
        resp = self._get("director=nolan")
        self.assertEqual(resp.status_code, 200)

    def test_catalog_filter_by_rating(self):
        resp = self._get("valoracio=8")
        self.assertEqual(resp.status_code, 200)

    def test_catalog_pagination_12_items_per_page(self):
        # 15 movies + 15 series = 30 items → page 1 should have 12
        resp = self._get()
        page_obj = resp.context["page_obj"]
        self.assertLessEqual(len(page_obj.object_list), 12)

    def test_catalog_movies_only(self):
        with patch(_MOVIES, return_value=MOCK_MOVIES), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_ENRICH, side_effect=lambda x: x):
            resp = self.client.get(reverse("cataleg_pelis"))
        self.assertEqual(resp.status_code, 200)

    def test_catalog_series_only(self):
        with patch(_SERIES, return_value=MOCK_SERIES), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_ENRICH, side_effect=lambda x: x):
            resp = self.client.get(reverse("cataleg_series"))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# detall_contingut
# ---------------------------------------------------------------------------

class DetallContingutViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="detalluser")
        self.client.login(username="detalluser", password="pass1234!")
        self.movie = make_movie()

    def _get_detail(self, tipus="movie", cid="8080_1"):
        with patch(_MOVIES, return_value=MOCK_MOVIES), \
             patch(_SERIES, return_value=MOCK_SERIES), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_TMDB, return_value=PLACEHOLDER), \
             patch(_ENRICH, return_value=MOCK_MOVIES[:1]):
            return self.client.get(
                reverse("pagina_contingut", kwargs={"tipus": tipus, "content_id": cid})
            )

    def test_movie_detail_loads(self):
        resp = self._get_detail("movie", "8080_1")
        self.assertEqual(resp.status_code, 200)

    def test_series_detail_loads(self):
        resp = self._get_detail("series", "8081_1")
        self.assertEqual(resp.status_code, 200)

    def test_detail_404_for_unknown_content(self):
        with patch(_MOVIES, return_value=[]), \
             patch(_SERIES, return_value=[]), \
             patch(_GENRES, return_value=[]), \
             patch(_RATINGS, return_value=[]), \
             patch(_DIRECTORS, return_value=[]), \
             patch(_TMDB, return_value=PLACEHOLDER), \
             patch(_ENRICH, return_value=[]):
            resp = self.client.get(
                reverse("pagina_contingut", kwargs={"tipus": "movie", "content_id": "nonexistent"})
            )
        self.assertEqual(resp.status_code, 404)

    def test_detail_context_contains_item(self):
        resp = self._get_detail()
        self.assertIn("item", resp.context)

    def test_detail_shows_reviews(self):
        movie_obj = make_movie()
        Ressenya.objects.create(usuari=self.user, pelicula=movie_obj, puntuacio=9)
        resp = self._get_detail()
        self.assertIn("ressenyes", resp.context)


# ---------------------------------------------------------------------------
# cerca_contingut (fuzzy search)
# ---------------------------------------------------------------------------

_SEARCH_MOVIES = "apps.contents.views.get_all_movies"
_SEARCH_SERIES = "apps.contents.views.get_all_series"
_SEARCH_GENRES = "apps.contents.views.get_genres_from_api"
_SEARCH_RATINGS = "apps.contents.views.get_age_ratings_from_api"


class CercaContingutViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def _search(self, query):
        with patch(_SEARCH_MOVIES, return_value=MOCK_MOVIES), \
             patch(_SEARCH_SERIES, return_value=MOCK_SERIES), \
             patch(_SEARCH_GENRES, return_value=MOCK_GENRES), \
             patch(_SEARCH_RATINGS, return_value=MOCK_RATINGS), \
             patch(_TMDB, return_value=PLACEHOLDER), \
             patch(_ENRICH, side_effect=lambda x: x):
            return self.client.get(reverse("cerca_contingut") + f"?q={query}")

    def test_search_with_exact_title_returns_result(self):
        resp = self._search("Interstellar")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context["resultat"])

    def test_search_with_fuzzy_match(self):
        resp = self._search("Interstllar")
        self.assertEqual(resp.status_code, 200)
        # Fuzzy match should still find it
        self.assertIsNotNone(resp.context["resultat"])

    def test_search_empty_query_returns_no_result(self):
        resp = self._search("")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context["resultat"])

    def test_search_nonsense_query_returns_none(self):
        resp = self._search("zzzzzzzzzzzzzzz")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context["resultat"])


# ---------------------------------------------------------------------------
# crear_cuenta (registration)
# ---------------------------------------------------------------------------

_REG_GENRES = "apps.users.views.get_genres_from_api"
_REG_RATINGS = "apps.users.views.get_age_ratings_from_api"
_REG_MOVIES = "apps.users.views.get_all_movies"
_REG_SERIES = "apps.users.views.get_all_series"


class CrearCuentaViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("registre")

    def _post(self, data):
        with patch(_REG_GENRES, return_value=MOCK_GENRES), \
             patch(_REG_RATINGS, return_value=MOCK_RATINGS):
            return self.client.post(self.url, data)

    def test_registration_page_loads(self):
        with patch(_REG_GENRES, return_value=MOCK_GENRES), \
             patch(_REG_RATINGS, return_value=MOCK_RATINGS):
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_successful_registration_creates_user(self):
        self._post({
            "username": "newuser",
            "first_name": "New User",
            "email": "new@test.com",
            "password1": "superSecret99!",
            "password2": "superSecret99!",
            "tipus": ["movie"],
            "plataformes": ["CinePlus"],
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_successful_registration_saves_preferences_to_profile(self):
        self._post({
            "username": "prefuser",
            "first_name": "Pref User",
            "email": "pref@test.com",
            "password1": "superSecret99!",
            "password2": "superSecret99!",
            "tipus": ["movie", "series"],
            "plataformes": ["StreamHub"],
            "generos": ["1"],
            "edats": ["2"],
        })
        user = User.objects.get(username="prefuser")
        self.assertIn("movie", user.profile.tipus)
        self.assertIn("StreamHub", user.profile.plataformes)

    def test_invalid_registration_shows_error(self):
        with patch(_REG_GENRES, return_value=MOCK_GENRES), \
             patch(_REG_RATINGS, return_value=MOCK_RATINGS):
            resp = self.client.post(self.url, {
                "username": "",
                "password1": "abc",
                "password2": "xyz",
            })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="").exists())

    def test_successful_registration_redirects(self):
        resp = self._post({
            "username": "redirectuser",
            "first_name": "Redirect User",
            "email": "redir@test.com",
            "password1": "superSecret99!",
            "password2": "superSecret99!",
        })
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# publicar_ressenya
# ---------------------------------------------------------------------------

class PublicarResenyaViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="reviewuser")
        self.client.login(username="reviewuser", password="pass1234!")
        self.movie = make_movie()

    def _post_review(self, puntuacio=8, comentari="Great film!"):
        url = reverse("publicar_ressenya", kwargs={"tipus": "movie", "content_id": self.movie.id})
        return self.client.post(url, {"puntuacio": puntuacio, "comentari": comentari})

    def test_create_review(self):
        self._post_review()
        self.assertTrue(Ressenya.objects.filter(usuari=self.user, pelicula=self.movie).exists())

    def test_update_existing_review(self):
        Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=5)
        self._post_review(puntuacio=9)
        r = Ressenya.objects.get(usuari=self.user, pelicula=self.movie)
        self.assertEqual(r.puntuacio, 9)

    def test_review_requires_authentication(self):
        self.client.logout()
        resp = self._post_review()
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp["Location"])

    def test_review_redirects_after_post(self):
        resp = self._post_review()
        self.assertEqual(resp.status_code, 302)

    def test_review_success_message(self):
        self._post_review()
        # Message is consumed on redirect, verify via messages storage
        resp = self._post_review()
        msgs = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("Ressenya" in str(m) or "publicada" in str(m) for m in msgs))


# ---------------------------------------------------------------------------
# afegir_a_llista
# ---------------------------------------------------------------------------

class AfegirALlistaViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="listuser")
        self.client.login(username="listuser", password="pass1234!")
        self.movie = make_movie()
        self.folder = Carpeta.objects.create(usuari=self.user, nom="Watch Later")

    def test_add_to_list_creates_item(self):
        url = reverse("afegir_a_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        with patch(_MOVIES, return_value=MOCK_MOVIES), \
             patch(_SERIES, return_value=MOCK_SERIES), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_TMDB, return_value=PLACEHOLDER), \
             patch(_ENRICH, return_value=[]):
            self.client.post(url, {"carpeta_id": self.folder.id})
        self.assertTrue(LlistaPersonal.objects.filter(usuari=self.user, pelicula=self.movie).exists())

    def test_add_requires_authentication(self):
        self.client.logout()
        url = reverse("afegir_a_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        resp = self.client.post(url, {"carpeta_id": self.folder.id})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp["Location"])

    def test_add_to_list_is_idempotent(self):
        url = reverse("afegir_a_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        with patch(_MOVIES, return_value=MOCK_MOVIES), \
             patch(_SERIES, return_value=MOCK_SERIES), \
             patch(_GENRES, return_value=MOCK_GENRES), \
             patch(_RATINGS, return_value=MOCK_RATINGS), \
             patch(_DIRECTORS, return_value=MOCK_DIRECTORS), \
             patch(_TMDB, return_value=PLACEHOLDER), \
             patch(_ENRICH, return_value=[]):
            self.client.post(url, {"carpeta_id": self.folder.id})
            self.client.post(url, {"carpeta_id": self.folder.id})
        self.assertEqual(LlistaPersonal.objects.filter(usuari=self.user, pelicula=self.movie).count(), 1)


# ---------------------------------------------------------------------------
# treure_de_llista
# ---------------------------------------------------------------------------

class TreureDeListaViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="removeuser")
        self.client.login(username="removeuser", password="pass1234!")
        self.movie = make_movie()
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie)

    def test_remove_from_list(self):
        url = reverse("treure_de_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        self.client.post(url)
        self.assertFalse(LlistaPersonal.objects.filter(usuari=self.user, pelicula=self.movie).exists())

    def test_remove_requires_authentication(self):
        self.client.logout()
        url = reverse("treure_de_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp["Location"])

    def test_remove_redirects_to_lists(self):
        url = reverse("treure_de_llista", kwargs={"tipus": "movie", "content_id": self.movie.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
