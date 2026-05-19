"""
Model tests for StreamSync.
Covers: Pelicula, Ressenya, LlistaPersonal, Views, Profile
"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.analytics.models import Views
from apps.contents.models import Genere, Pelicula
from apps.lists.models import Carpeta, LlistaPersonal
from apps.reviews.models import Ressenya, Feedback
from apps.users.models.models import Profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_movie(pk="test_1", titol="Test Movie", tipus="movie", **kwargs):
    defaults = dict(id=pk, titol=titol, tipus=tipus, valoracio=7.5)
    defaults.update(kwargs)
    return Pelicula.objects.create(**defaults)


def make_user(username="testuser", password="pass1234!", **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


# ---------------------------------------------------------------------------
# Pelicula / Contingut
# ---------------------------------------------------------------------------

class PeliculaModelTest(TestCase):

    def test_create_movie(self):
        movie = make_movie()
        self.assertEqual(movie.titol, "Test Movie")
        self.assertEqual(movie.tipus, "movie")

    def test_str_representation(self):
        movie = make_movie(titol="Inception")
        self.assertEqual(str(movie), "Inception")

    def test_default_valoracio(self):
        movie = Pelicula.objects.create(id="m2", titol="No Rating")
        self.assertEqual(movie.valoracio, 0.0)

    def test_tipus_choices_movie(self):
        movie = make_movie(tipus="movie")
        self.assertEqual(movie.tipus, "movie")

    def test_tipus_choices_series(self):
        movie = make_movie(pk="s1", tipus="series")
        self.assertEqual(movie.tipus, "series")

    def test_optional_fields_are_nullable(self):
        movie = Pelicula.objects.create(id="m3", titol="Minimal")
        self.assertIsNone(movie.director)
        self.assertIsNone(movie.sinopsi)
        self.assertIsNone(movie.any)
        self.assertIsNone(movie.imatge)

    def test_genre_many_to_many(self):
        movie = make_movie()
        genre = Genere.objects.create(nom="Thriller")
        movie.generes.add(genre)
        self.assertIn(genre, movie.generes.all())


class GenereModelTest(TestCase):

    def test_create_genre(self):
        genre = Genere.objects.create(nom="Drama")
        self.assertEqual(str(genre), "Drama")

    def test_unique_genre_name(self):
        Genere.objects.create(nom="Comedy")
        with self.assertRaises(IntegrityError):
            Genere.objects.create(nom="Comedy")


# ---------------------------------------------------------------------------
# Ressenya
# ---------------------------------------------------------------------------

class ResenyaModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()

    def test_create_review(self):
        r = Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=8)
        self.assertEqual(r.puntuacio, 8)

    def test_str_representation(self):
        r = Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=7)
        self.assertIn(self.user.username, str(r))
        self.assertIn(self.movie.titol, str(r))
        self.assertIn("7/10", str(r))

    def test_unique_constraint_per_user_and_content(self):
        Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=5)
        with self.assertRaises(IntegrityError):
            Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=6)

    def test_score_min_boundary(self):
        r = Ressenya(usuari=self.user, pelicula=self.movie, puntuacio=0)
        try:
            r.full_clean()  # Should not raise
        except ValidationError:
            self.fail("Score of 0 should be valid")

    def test_score_max_boundary(self):
        r = Ressenya(usuari=self.user, pelicula=self.movie, puntuacio=10)
        try:
            r.full_clean()
        except ValidationError:
            self.fail("Score of 10 should be valid")

    def test_score_below_min_fails(self):
        r = Ressenya(usuari=self.user, pelicula=self.movie, puntuacio=-1)
        with self.assertRaises(ValidationError):
            r.full_clean()

    def test_score_above_max_fails(self):
        r = Ressenya(usuari=self.user, pelicula=self.movie, puntuacio=11)
        with self.assertRaises(ValidationError):
            r.full_clean()

    def test_review_cascade_delete_with_user(self):
        Ressenya.objects.create(usuari=self.user, pelicula=self.movie, puntuacio=5)
        self.user.delete()
        self.assertEqual(Ressenya.objects.count(), 0)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackModelTest(TestCase):

    def test_create_feedback(self):
        fb = Feedback.objects.create(
            titol="App crash", descripcio="It crashed on login", tipus="error"
        )
        self.assertEqual(fb.tipus, "error")
        self.assertIn("error", str(fb))

    def test_feedback_without_rating(self):
        fb = Feedback.objects.create(
            titol="Suggestion", descripcio="Add dark mode", tipus="suggestion"
        )
        self.assertIsNone(fb.rating)


# ---------------------------------------------------------------------------
# LlistaPersonal (Saved Content)
# ---------------------------------------------------------------------------

class LlistaPersonalModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()
        self.folder = Carpeta.objects.create(usuari=self.user, nom="My List")

    def test_create_list_item(self):
        item = LlistaPersonal.objects.create(
            usuari=self.user, pelicula=self.movie, carpeta=self.folder
        )
        self.assertEqual(item.usuari, self.user)
        self.assertEqual(item.pelicula, self.movie)

    def test_unique_constraint_per_user_content_list(self):
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie, carpeta=self.folder)
        with self.assertRaises(IntegrityError):
            LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie, carpeta=self.folder)

    def test_same_content_in_different_folders(self):
        folder2 = Carpeta.objects.create(usuari=self.user, nom="Favourites")
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie, carpeta=self.folder)
        # Should not raise
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie, carpeta=folder2)
        self.assertEqual(LlistaPersonal.objects.count(), 2)

    def test_list_item_without_folder(self):
        item = LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie)
        self.assertIsNone(item.carpeta)

    def test_cascade_delete_with_user(self):
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.movie)
        self.user.delete()
        self.assertEqual(LlistaPersonal.objects.count(), 0)


class CarpetaModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_folder(self):
        folder = Carpeta.objects.create(usuari=self.user, nom="Watch Later")
        self.assertEqual(str(folder), f"Watch Later ({self.user.username})")

    def test_default_icon_and_color(self):
        folder = Carpeta.objects.create(usuari=self.user, nom="Test")
        self.assertEqual(folder.icona, "bi-star-fill")
        self.assertEqual(folder.color, "#8a2be2")


# ---------------------------------------------------------------------------
# Views (Visualitzacio)
# ---------------------------------------------------------------------------

class ViewsModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()

    def test_create_view_record(self):
        v = Views.objects.create(usuari=self.user, pelicula=self.movie, count=0)
        self.assertEqual(v.count, 0)

    def test_increment_count(self):
        v = Views.objects.create(usuari=self.user, pelicula=self.movie, count=0)
        v.count += 1
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.count, 1)

    def test_repeated_views_increment(self):
        v, _ = Views.objects.get_or_create(usuari=self.user, pelicula=self.movie, defaults={"count": 0})
        for _ in range(5):
            v.count += 1
            v.save()
        v.refresh_from_db()
        self.assertEqual(v.count, 5)

    def test_cascade_delete_with_movie(self):
        Views.objects.create(usuari=self.user, pelicula=self.movie, count=3)
        self.movie.delete()
        self.assertEqual(Views.objects.count(), 0)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileModelTest(TestCase):

    def test_profile_auto_created_via_signal(self):
        user = make_user(username="signaluser")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str(self):
        user = make_user(username="struser")
        profile = user.profile
        self.assertIn("struser", str(profile))

    def test_profile_default_fields_are_empty_lists(self):
        user = make_user(username="emptyprefs")
        profile = user.profile
        self.assertEqual(profile.tipus, [])
        self.assertEqual(profile.plataformes, [])
        self.assertEqual(profile.generes, [])
        self.assertEqual(profile.edat_rating, [])

    def test_profile_save_preferences(self):
        user = make_user(username="prefuser")
        profile = user.profile
        profile.tipus = ["movie"]
        profile.plataformes = ["CinePlus"]
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.tipus, ["movie"])
        self.assertEqual(profile.plataformes, ["CinePlus"])

    def test_profile_cascade_delete_with_user(self):
        user = make_user(username="deluser")
        user.delete()
        self.assertEqual(Profile.objects.filter(user__username="deluser").count(), 0)

    def test_only_one_profile_per_user_via_signal(self):
        user = make_user(username="oneprofile")
        # Triggering signal again should not duplicate
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User as AuthUser
        post_save.send(sender=AuthUser, instance=user, created=True)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
