from django.test import TestCase

# Create your tests here.

from django.test import TestCase
from apps.analytics.services import (
    get_platform_metrics,
    calculate_view_trend,
    get_top_content,
    build_dashboard_context
)


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