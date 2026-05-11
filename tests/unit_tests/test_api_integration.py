from django.test import TestCase
from unittest.mock import patch, MagicMock
from users.views import get_all_movies, get_all_series, get_imatge_tmdb, enriquir_imatges_tmdb
import requests
from concurrent.futures import ThreadPoolExecutor

# Mock the API_CONFIG and TMDB_API_KEY for consistent testing
@patch('users.views.API_CONFIG', {'http://localhost:8080': 'key1'})
@patch('users.views.TMDB_API_KEY', 'mock_tmdb_key')
class ApiIntegrationTestCase(TestCase):

    @patch('requests.get')
    def test_get_all_movies_timeout(self, mock_get):
        """Test get_all_movies() handles API timeout gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout
        movies = get_all_movies()
        self.assertEqual(movies, []) # Should return an empty list on timeout

    @patch('requests.get')
    def test_get_all_series_timeout(self, mock_get):
        """Test get_all_series() handles API timeout gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout
        series = get_all_series()
        self.assertEqual(series, []) # Should return an empty list on timeout

    @patch('requests.get')
    def test_get_imatge_tmdb_valid_url(self, mock_get):
        """Test get_imatge_tmdb() returns a valid URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"poster_path": "/test_path.jpg"}]
        }
        mock_get.return_value = mock_response
        
        image_url = get_imatge_tmdb("Test Title")
        self.assertEqual(image_url, "https://image.tmdb.org/t/p/w500/test_path.jpg")

    @patch('requests.get')
    def test_get_imatge_tmdb_placeholder_on_failure(self, mock_get):
        """Test get_imatge_tmdb() returns a placeholder on API failure or no results."""
        # Simulate API error
        mock_get.side_effect = requests.exceptions.RequestException
        image_url_error = get_imatge_tmdb("Test Title")
        self.assertEqual(image_url_error, 'https://via.placeholder.com/300x450')

        # Simulate no results
        mock_get.side_effect = None
        mock_response_no_results = MagicMock()
        mock_response_no_results.status_code = 200
        mock_response_no_results.json.return_value = {"results": []}
        mock_get.return_value = mock_response_no_results
        image_url_no_results = get_imatge_tmdb("Test Title")
        self.assertEqual(image_url_no_results, 'https://via.placeholder.com/300x450')

    @patch('users.views.get_imatge_tmdb')
    @patch('concurrent.futures.ThreadPoolExecutor', autospec=True)
    def test_enriquir_imatges_tmdb_fetches_in_parallel(self, mock_executor, mock_get_imatge_tmdb):
        """Test enriquir_imatges_tmdb() fetches images in parallel without errors."""
        mock_get_imatge_tmdb.side_effect = lambda title: f"image_for_{title}"
        
        # Mock the executor to run tasks synchronously for testing purposes
        mock_executor.return_value.__enter__.return_value.map.side_effect = lambda func, iterable: [func(item) for item in iterable]

        test_list = [
            {'titol': 'Movie A'},
            {'titol': 'Movie B'}
        ]
        
        enriched_list = enriquir_imatges_tmdb(test_list)
        
        self.assertEqual(len(enriched_list), 2)
        self.assertEqual(enriched_list[0]['imatge'], 'image_for_Movie A')
        self.assertEqual(enriched_list[1]['imatge'], 'image_for_Movie B')
        mock_get_imatge_tmdb.assert_any_call('Movie A')
        mock_get_imatge_tmdb.assert_any_call('Movie B')
        self.assertEqual(mock_get_imatge_tmdb.call_count, 2)
