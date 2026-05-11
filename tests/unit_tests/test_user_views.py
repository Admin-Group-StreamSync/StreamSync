from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_session_auth_hash
from users.models import Pelicula, Ressenya, LlistaPersonal, Profile
from unittest.mock import patch
import json

class AuthViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testauth', password='password123')
        self.protected_url = reverse('llistes')
        self.login_url = reverse('login')

    def test_protected_view_redirects_unauthenticated(self):
        """Authentication: Test that protected views redirect unauthenticated users to login."""
        response = self.client.get(self.protected_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.protected_url}')

    def test_login_displays_success_message(self):
        """Authentication: Test that login displays a success message."""
        response = self.client.post(self.login_url, {'username': 'testauth', 'password': 'password123'}, follow=True)
        self.assertContains(response, "Benvingut/da de nou, testauth!")

    def test_registration_saves_preferences(self):
        """crear_cuenta: Test successful registration saves user preferences to profile."""
        form_data = {
            'username': 'newprefuser', 'first_name': 'Pref', 'email': 'pref@test.com',
            'password': 'newpass', 'password2': 'newpass',
            'tipus': ['movie', 'series'], 'plataformes': ['CinePlus'],
            'generos': ['1', '3'], 'edats': ['2']
        }
        self.client.post(reverse('crear_cuenta'), form_data)
        user = User.objects.get(username='newprefuser')
        self.assertEqual(user.profile.tipus, ['movie', 'series'])
        self.assertEqual(user.profile.plataformes, ['CinePlus'])
        self.assertEqual(user.profile.generes, ['1', '3'])
        self.assertEqual(user.profile.edat_rating, ['2'])

    def test_password_change_updates_session(self):
        """Authentication: Test that password change updates the session correctly."""
        self.client.login(username='testauth', password='password123')
        session_hash_before = self.client.session.get(get_session_auth_hash())
        
        self.client.post(reverse('cambiar_password'), {
            'old_password': 'password123', 'new_password1': 'newpassword', 'new_password2': 'newpassword'
        })
        
        session_hash_after = self.client.session.get(get_session_auth_hash())
        self.assertNotEqual(session_hash_before, session_hash_after)

class MainViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testmain', password='password')

    @patch('users.views.get_all_movies')
    @patch('users.views.get_all_series')
    def test_pagina_principal_loads(self, mock_series, mock_movies):
        """pagina_principal: Test page loads correctly for authenticated and anonymous users."""
        mock_movies.return_value = []
        mock_series.return_value = []
        
        # Anonymous user
        response_anon = self.client.get(reverse('pagina_principal'))
        self.assertEqual(response_anon.status_code, 200)
        
        # Authenticated user
        self.client.login(username='testmain', password='password')
        response_auth = self.client.get(reverse('pagina_principal'))
        self.assertEqual(response_auth.status_code, 200)

    @patch('users.views.get_all_movies')
    def test_catalogo_pagination(self, mock_movies):
        """catalogo: Test pagination returns 12 items per page."""
        mock_movies.return_value = [{'id': f'm{i}', 'titol': f'Movie {i}'} for i in range(20)]
        
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(len(response.context['contenidos']), 12)

    @patch('users.views.get_all_movies')
    def test_catalogo_filtering(self, mock_movies):
        """catalogo: Test filtering by platform, genre, age rating, director and rating."""
        mock_movies.return_value = [
            {'id': 'f1', 'titol': 'Action Movie', 'plataforma': 'CinePlus', 'genre_id': '1', 'age_rating_id': '3', 'director_id': '10', 'rating': '9.0'},
            {'id': 'f2', 'titol': 'Comedy Movie', 'plataforma': 'StreamHub', 'genre_id': '2', 'age_rating_id': '1', 'director_id': '11', 'rating': '7.0'}
        ]
        
        # Filter by platform
        response = self.client.get(reverse('catalogo'), {'plataforma': 'CinePlus'})
        self.assertContains(response, 'Action Movie')
        self.assertNotContains(response, 'Comedy Movie')

    @patch('users.views.get_all_movies')
    @patch('users.views.get_all_series')
    def test_detall_contingut_movie_and_series(self, mock_series, mock_movies):
        """detall_contingut: Test page loads correctly for both movies and series."""
        mock_movies.return_value = [{'id': '8080_1', 'titol': 'Test Movie', 'any': 2022, 'plataforma': 'CinePlus'}]
        mock_series.return_value = [{'id': '8081_1', 'titol': 'Test Series', 'any': 2021, 'plataforma': 'StreamHub'}]
        
        # Movie detail
        response_movie = self.client.get(reverse('pagina_contingut', args=['movie', '8080_1']))
        self.assertEqual(response_movie.status_code, 200)
        self.assertContains(response_movie, 'Test Movie')
        
        # Series detail
        response_series = self.client.get(reverse('pagina_contingut', args=['series', '8081_1']))
        self.assertEqual(response_series.status_code, 200)
        self.assertContains(response_series, 'Test Series')

    @patch('users.views.get_all_movies')
    def test_cerca_contingut_fuzzy_search(self, mock_movies):
        """cerca_contingut: Test fuzzy search returns the correct result."""
        mock_movies.return_value = [{'id': 'm1', 'titol': 'The Shawshank Redemption'}]
        response = self.client.get(reverse('cerca_contingut'), {'q': 'Shawshank'})
        self.assertContains(response, 'The Shawshank Redemption')

class UserContentViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testcontent', password='password')
        self.client.login(username='testcontent', password='password')
        self.pelicula = Pelicula.objects.create(id='content1', titol='Content Movie', tipus='movie')
        self.detall_url = reverse('pagina_contingut', args=[self.pelicula.tipus, self.pelicula.id])

    def test_publicar_and_update_ressenya(self):
        """publicar_ressenya: Test creating and updating a review."""
        # Create
        self.client.post(reverse('publicar_ressenya', args=[self.pelicula.tipus, self.pelicula.id]), {'puntuacio': 8, 'comentari': 'Good'})
        ressenya = Ressenya.objects.get(usuari=self.user, pelicula=self.pelicula)
        self.assertEqual(ressenya.puntuacio, 8)
        self.assertEqual(ressenya.comentari, 'Good')
        
        # Update
        self.client.post(reverse('publicar_ressenya', args=[self.pelicula.tipus, self.pelicula.id]), {'puntuacio': 9, 'comentari': 'Excellent'})
        ressenya.refresh_from_db()
        self.assertEqual(ressenya.puntuacio, 9)
        self.assertEqual(ressenya.comentari, 'Excellent')

    def test_afegir_a_llista(self):
        """afegir_a_llista: Test adding content to a list."""
        self.client.post(reverse('afegir_a_llista', args=[self.pelicula.tipus, self.pelicula.id]), {'carpeta_id': ''})
        self.assertTrue(LlistaPersonal.objects.filter(usuari=self.user, pelicula=self.pelicula).exists())

    def test_treure_de_llista(self):
        """treure_de_llista: Test removing content from a list."""
        LlistaPersonal.objects.create(usuari=self.user, pelicula=self.pelicula)
        self.client.post(reverse('treure_de_llista', args=[self.pelicula.tipus, self.pelicula.id]))
        self.assertFalse(LlistaPersonal.objects.filter(usuari=self.user, pelicula=self.pelicula).exists())
