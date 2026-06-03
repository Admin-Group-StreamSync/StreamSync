from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from users.models import Profile, Pelicula, Carpeta, LlistaPersonal, Ressenya, Views

class ProfileModelTestCase(TestCase):
    def test_profile_creation_signal(self):
        """Profile: Test automatic creation via signal when a new User is created."""
        user = User.objects.create_user(username='test_signal_user', password='password')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)
        self.assertEqual(str(user.profile), f"Perfil de {user.username} (User)")

    def test_profile_manager_de_choices(self):
        """Profile: Test manager_de field validation."""
        user = User.objects.create_user(username='test_manager_choices', password='password')
        profile = user.profile

        # Test valid choices
        profile.manager_de = 'CinePlus'
        profile.full_clean() # Should not raise ValidationError
        profile.manager_de = 'StreamHub'
        profile.full_clean() # Should not raise ValidationError
        profile.manager_de = 'PlayMax'
        profile.full_clean() # Should not raise ValidationError
        profile.manager_de = None
        profile.full_clean() # Should not raise ValidationError

        # Test invalid choice
        with self.assertRaises(ValidationError):
            profile.manager_de = 'InvalidPlatform'
            profile.full_clean()


class PeliculaModelTestCase(TestCase):
    def test_pelicula_creation(self):
        """Pelicula (Contingut): Test creation and string representation."""
        pelicula = Pelicula.objects.create(id='peli_test_1', titol='Test Movie', any=2023, valoracio=8.5, tipus='movie')
        self.assertEqual(str(pelicula), 'Test Movie')
        self.assertEqual(pelicula.valoracio, 8.5)

    def test_pelicula_tipus_choices(self):
        """Pelicula: Test tipus field validation."""
        # Test valid choices
        pelicula_movie = Pelicula(id='peli_type_1', titol='Movie Type', tipus='movie')
        pelicula_movie.full_clean() # Should not raise ValidationError
        pelicula_series = Pelicula(id='peli_type_2', titol='Series Type', tipus='series')
        pelicula_series.full_clean() # Should not raise ValidationError

        # Test invalid choice
        with self.assertRaises(ValidationError):
            pelicula_invalid = Pelicula(id='peli_type_3', titol='Invalid Type', tipus='invalid')
            pelicula_invalid.full_clean()


class CarpetaModelTestCase(TestCase):
    def test_carpeta_creation(self):
        """Carpeta (LlistaUsuari): Test creation and relation to User."""
        user = User.objects.create_user(username='test_carpeta_user', password='password')
        carpeta = Carpeta.objects.create(usuari=user, nom='My Favorites')
        self.assertEqual(carpeta.usuari, user)
        self.assertEqual(str(carpeta), f"My Favorites ({user.username})")

class LlistaPersonalModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_llista_user', password='password')
        self.pelicula = Pelicula.objects.create(id='peli_llista_1', titol='Movie for List')
        self.carpeta = Carpeta.objects.create(usuari=self.user, nom='Watchlist')

    def test_unique_constraint_per_user_content_and_list(self):
        """LlistaPersonal (ContingutDesat): Test unique constraint per user, content and list."""
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.pelicula, carpeta=self.carpeta)
        with self.assertRaises(IntegrityError):
            LlistaPersonal.objects.create(usuari=self.user, pelicula=self.pelicula, carpeta=self.carpeta)

class RessenyaModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_ressenya_user', password='password')
        self.pelicula = Pelicula.objects.create(id='peli_ressenya_1', titol='Movie for Review')

    def test_unique_constraint_per_user_and_content(self):
        """Ressenya: Test unique constraint per user and content."""
        Ressenya.objects.create(usuari=self.user, pelicula=self.pelicula, puntuacio=5)
        with self.assertRaises(IntegrityError):
            Ressenya.objects.create(usuari=self.user, pelicula=self.pelicula, puntuacio=7)

    def test_score_range_validation(self):
        """Ressenya: Test score range validation (0-10)."""
        # Test valid scores
        ressenya_valid_low = Ressenya(usuari=self.user, pelicula=self.pelicula, puntuacio=0)
        ressenya_valid_low.full_clean()  # Should not raise ValidationError
        ressenya_valid_high = Ressenya(usuari=self.user, pelicula=self.pelicula, puntuacio=10)
        ressenya_valid_high.full_clean() # Should not raise ValidationError

        # Test invalid scores
        with self.assertRaises(ValidationError):
            ressenya_invalid_low = Ressenya(usuari=self.user, pelicula=self.pelicula, puntuacio=-1)
            ressenya_invalid_low.full_clean()
        
        with self.assertRaises(ValidationError):
            ressenya_invalid_high = Ressenya(usuari=self.user, pelicula=self.pelicula, puntuacio=11)
            ressenya_invalid_high.full_clean()

class ViewsModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_views_user', password='password')
        self.pelicula = Pelicula.objects.create(id='peli_views_1', titol='Movie for Views')

    def test_view_creation_and_counter(self):
        """Visualitzacio: Test counter increment on repeated views (logic is in view)."""
        # The counter logic is in the view, but we test the model field here.
        view = Views.objects.create(usuari=self.user, pelicula=self.pelicula, count=1)
        self.assertEqual(view.count, 1)
        view.count += 1
        view.save()
        self.assertEqual(view.count, 2)
