from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase

from apps.analytics.models import Views
from apps.analytics.services import (
    add_view,
    get_platform_metrics,
    calculate_view_trend,
    get_top_content,
    build_dashboard_context
)
from apps.contents.models import Pelicula


class TestAnalyticsServices(TestCase):

    def test_get_platform_metrics(self):
        """Test platform metrics retrieval."""
        metrics = get_platform_metrics('CinePlus')
        self.assertIn('average_rating', metrics)
        self.assertIn('total_reviews', metrics)
        self.assertIsInstance(metrics['average_rating'], (int, float))

    def test_calculate_view_trend(self):
        """Test view trend calculation."""
        trend = calculate_view_trend('CinePlus')
        self.assertIn('current', trend)
        self.assertIn('trend', trend)
        self.assertIsInstance(trend['trend'], float)

    def test_get_top_content(self):
        """Test top content retrieval."""
        top = get_top_content('CinePlus', limit=5)
        self.assertIsInstance(top, list)
        self.assertLessEqual(len(top), 5)
        if top:
            self.assertIn('titol', top[0])
            self.assertIn('vistes_totals', top[0])

    def test_build_dashboard_context(self):
        """Test complete dashboard context."""
        context = build_dashboard_context('CinePlus')
        required_keys = ['plataforma', 'metricas', 'tendencias', 'top_contingut']
        for key in required_keys:
            self.assertIn(key, context)

    def test_views_are_counted_for_selected_platform(self):
        """A title available on several platforms must count the selected play platform."""
        user = User.objects.create_user(username='viewer', password='pass')
        film = Pelicula.objects.create(
            id='movie-1',
            titol='Shared Movie',
            plataforma='CinePlus',
            tipus='movie'
        )
        request = SimpleNamespace(user=user)

        add_view(request, film, 'StreamHub')
        add_view(request, film, 'PlayMax')
        add_view(request, film, 'PlayMax')

        self.assertEqual(Views.objects.get(plataforma='StreamHub').count, 1)
        self.assertEqual(Views.objects.get(plataforma='PlayMax').count, 2)
        self.assertEqual(get_platform_metrics('StreamHub')['total_views'], 1)
        self.assertEqual(get_platform_metrics('PlayMax')['total_views'], 2)
        self.assertEqual(get_platform_metrics('CinePlus')['total_views'], 0)
