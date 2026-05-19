"""
Analytics Services Module.

This module contains all business logic for analytics operations,
following Clean Architecture principles with clear separation of concerns.
"""
import logging
from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone

from apps.analytics.models import Views
from apps.contents.models import Pelicula
from apps.contents.services.content_service import (
    get_all_movies,
    get_all_series,
    get_age_ratings_from_api,
    get_genres_from_api
)
from apps.lists.models import LlistaPersonal
from apps.reviews.models import Ressenya
from apps.users.models.models import Profile

logger = logging.getLogger(__name__)


# ============================================================================
# View Tracking Operations
# ============================================================================

def add_view(request, film):
    """
    Register or increment a view for a film.

    Args:
        request: Django HTTP request with authenticated user.
        film: Pelicula model instance.

    Returns:
        tuple: (Views object, created boolean).
    """
    view_reg, created = Views.objects.get_or_create(
        usuari=request.user,
        pelicula=film,
        defaults={"count": 0}
    )
    view_reg.count += 1
    view_reg.save()
    logger.info(f"View registered for film {film.titol} by user {request.user.username}")
    return view_reg, created


# ============================================================================
# Metrics Retrieval
# ============================================================================

def get_platform_metrics(platform_name):
    """
    Retrieve global metrics for a specific platform.

    Args:
        platform_name (str): Name of the platform.

    Returns:
        dict: Metrics including average rating, total reviews,
              saved items count, and interested users count.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)

    review_stats = Ressenya.objects.filter(
        pelicula__in=content
    ).aggregate(
        mitjana=Avg('puntuacio'),
        total=Count('id')
    )

    saved_count = LlistaPersonal.objects.filter(
        pelicula__in=content
    ).count()

    interested_users = sum(
        1 for profile in Profile.objects.all()
        if platform_name in profile.plataformes
    )

    return {
        'average_rating': review_stats['mitjana'] or 0,
        'total_reviews': review_stats['total'],
        'total_saved': saved_count,
        'interested_users': interested_users,
        'content_count': content.count()
    }


def _calculate_percentage_change(current, previous):
    """
    Calculate percentage change between two values.

    Args:
        current (int/float): Current period value.
        previous (int/float): Previous period value.

    Returns:
        float: Percentage change rounded to 1 decimal.
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


# ============================================================================
# Trend Calculations
# ============================================================================

def calculate_view_trend(platform_name):
    """
    Calculate views trend comparing last 30 vs 30-60 days.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Current views, previous views, and trend percentage.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_views = Views.objects.filter(
        pelicula__in=content,
        visualization_date__gte=thirty_days_ago
    ).aggregate(total=Sum('count'))['total'] or 0

    previous_views = Views.objects.filter(
        pelicula__in=content,
        visualization_date__gte=sixty_days_ago,
        visualization_date__lt=thirty_days_ago
    ).aggregate(total=Sum('count'))['total'] or 0

    trend = _calculate_percentage_change(current_views, previous_views)

    return {
        'current': current_views,
        'previous': previous_views,
        'trend': trend
    }


def calculate_review_trend(platform_name):
    """
    Calculate review activity trend comparing last 30 vs 30-60 days.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Current reviews count, previous count, and trend percentage.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_reviews = Ressenya.objects.filter(
        pelicula__in=content,
        data_publicacio__gte=thirty_days_ago
    ).count()

    previous_reviews = Ressenya.objects.filter(
        pelicula__in=content,
        data_publicacio__gte=sixty_days_ago,
        data_publicacio__lt=thirty_days_ago
    ).count()

    trend = _calculate_percentage_change(current_reviews, previous_reviews)

    return {
        'current': current_reviews,
        'previous': previous_reviews,
        'trend': trend
    }


def calculate_favorite_trend(platform_name):
    """
    Calculate saved items trend comparing last 30 vs 30-60 days.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Current saves, previous saves, and trend percentage.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_saved = LlistaPersonal.objects.filter(
        pelicula__in=content,
        data_afegida__gte=thirty_days_ago
    ).count()

    previous_saved = LlistaPersonal.objects.filter(
        pelicula__in=content,
        data_afegida__gte=sixty_days_ago,
        data_afegida__lt=thirty_days_ago
    ).count()

    trend = _calculate_percentage_change(current_saved, previous_saved)

    return {
        'current': current_saved,
        'previous': previous_saved,
        'trend': trend
    }


def calculate_rating_trend(platform_name):
    """
    Calculate average rating change comparing last 30 vs 30-60 days.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Current rating, previous rating, and absolute difference.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_rating = Ressenya.objects.filter(
        pelicula__in=content,
        data_publicacio__gte=thirty_days_ago
    ).aggregate(moyenne=Avg('puntuacio'))['moyenne'] or 0

    previous_rating = Ressenya.objects.filter(
        pelicula__in=content,
        data_publicacio__gte=sixty_days_ago,
        data_publicacio__lt=thirty_days_ago
    ).aggregate(moyenne=Avg('puntuacio'))['moyenne'] or 0

    trend = round(current_rating - previous_rating, 1)

    return {
        'current': current_rating,
        'previous': previous_rating,
        'trend': trend
    }


def calculate_user_trend(platform_name):
    """
    Calculate new user acquisition trend comparing last 30 vs 30-60 days.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Current new users, previous new users, and trend percentage.
    """
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_users = sum(
        1 for profile in Profile.objects.filter(user__date_joined__gte=thirty_days_ago)
        if platform_name in profile.plataformes
    )

    previous_users = sum(
        1 for profile in Profile.objects.filter(
            user__date_joined__gte=sixty_days_ago,
            user__date_joined__lt=thirty_days_ago
        )
        if platform_name in profile.plataformes
    )

    trend = _calculate_percentage_change(current_users, previous_users)

    return {
        'current': current_users,
        'previous': previous_users,
        'trend': trend
    }


# ============================================================================
# Top Content
# ============================================================================

def get_top_content(platform_name, limit=5):
    """
    Retrieve top viewed content for a platform.

    Args:
        platform_name (str): Platform identifier.
        limit (int): Maximum number of items to return. Defaults to 5.

    Returns:
        list: List of content dictionaries with view counts.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    top_content_db = content.annotate(
        vistes_totals=Sum('views__count')
    ).order_by('-vistes_totals')[:limit]

    result = []
    for item in top_content_db:
        result.append({
            'id': item.id,
            'titol': item.titol,
            'imatge': item.imatge,
            'any': item.any,
            'tipus': item.tipus,
            'rating': item.valoracio,
            'vistes_totals': item.vistes_totals or 0,
            'genre_id': '',
            'age_rating_id': '',
            'genere_nom': '',
            'edat_nom': '',
            'director_nom': ''
        })

    logger.info(f"Retrieved top {limit} content for platform {platform_name}")
    return result


# ============================================================================
# Chart Data: Content Distribution
# ============================================================================

def get_content_type_distribution(platform_name):
    """
    Get view distribution between movies and series.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Views count for movies and series.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)

    movies_views = Views.objects.filter(
        pelicula__in=content,
        pelicula__tipus='movie'
    ).aggregate(total=Sum('count'))['total'] or 0

    series_views = Views.objects.filter(
        pelicula__in=content,
        pelicula__tipus='series'
    ).aggregate(total=Sum('count'))['total'] or 0

    return {
        'movies': movies_views,
        'series': series_views
    }


# ============================================================================
# Chart Data: Genre Distribution
# ============================================================================

def get_genre_distribution(platform_name, limit=6):
    """
    Get view distribution across genres.

    Args:
        platform_name (str): Platform identifier.
        limit (int): Maximum genres to return. Defaults to 6.

    Returns:
        dict: Genre names and their view counts.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)

    try:
        all_api_content = get_all_movies() + get_all_series()
        genres_api = get_genres_from_api()
        genre_map = {str(g['id']): g['name'] for g in genres_api}

        views_per_genre = {}
        views_data = Views.objects.filter(pelicula__in=content)

        for view in views_data:
            api_item = next(
                (x for x in all_api_content if x['id'] == view.pelicula.id),
                None
            )

            if api_item:
                genre_id = str(api_item.get('genre_id'))
                genre_name = genre_map.get(genre_id, "Other")
            else:
                genre_name = "Other"

            views_per_genre[genre_name] = views_per_genre.get(genre_name, 0) + view.count

        sorted_genres = sorted(
            views_per_genre.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        genre_names = [g[0] for g in sorted_genres] if sorted_genres else ["Other"]
        genre_values = [g[1] for g in sorted_genres] if sorted_genres else [0]

        return {
            'labels': genre_names,
            'values': genre_values
        }

    except Exception as e:
        logger.error(f"Error calculating genre distribution: {str(e)}")
        return {
            'labels': ["Other"],
            'values': [0]
        }


# ============================================================================
# Chart Data: Evolution (Last 4 Months)
# ============================================================================

def get_evolution_data(platform_name):
    """
    Get views and user evolution for the last 4 months.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Labels, views data, and users data for the 4 months.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)
    now = timezone.now()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    labels = []
    views_values = []
    users_values = []

    for i in range(3, -1, -1):
        start_date = now - timedelta(days=30 * (i + 1))
        end_date = now - timedelta(days=30 * i)
        month_name = month_names[end_date.month - 1]
        labels.append(month_name)

        month_views = Views.objects.filter(
            pelicula__in=content,
            visualization_date__gte=start_date,
            visualization_date__lt=end_date
        ).aggregate(total=Sum('count'))['total'] or 0
        views_values.append(month_views)

        month_users = sum(
            1 for profile in Profile.objects.filter(
                user__date_joined__gte=start_date,
                user__date_joined__lt=end_date
            )
            if platform_name in profile.plataformes
        )
        users_values.append(month_users)

    return {
        'labels': labels,
        'views': views_values,
        'users': users_values
    }


# ============================================================================
# Chart Data: Age Rating Distribution
# ============================================================================

def get_age_rating_distribution(platform_name):
    """
    Get view distribution across age ratings.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Percentage distribution of views by age rating.
    """
    content = Pelicula.objects.filter(plataforma=platform_name)

    try:
        all_api_content = get_all_movies() + get_all_series()
        ratings_api = get_age_ratings_from_api()
        rating_map = {
            str(r['id']): (
                r.get('name') or r.get('title') or r.get('description') or "All"
            )
            for r in ratings_api
        }

        age_distribution = {'All': 0, '7+': 0, '13+': 0, '16+': 0, '18+': 0}
        total_views = 0

        views_data = Views.objects.filter(pelicula__in=content)

        for view in views_data:
            api_item = next(
                (x for x in all_api_content if x['id'] == view.pelicula.id),
                None
            )

            if api_item:
                rating_id = str(api_item.get('age_rating_id'))
                rating_name = rating_map.get(rating_id, "All").upper()
            else:
                rating_name = "ALL"

            if "18" in rating_name:
                age_distribution['18+'] += view.count
            elif "16" in rating_name:
                age_distribution['16+'] += view.count
            elif "13" in rating_name:
                age_distribution['13+'] += view.count
            elif "7" in rating_name:
                age_distribution['7+'] += view.count
            else:
                age_distribution['All'] += view.count

            total_views += view.count

        divisor = total_views if total_views > 0 else 1

        return {
            'all': round((age_distribution['All'] / divisor) * 100),
            'm7': round((age_distribution['7+'] / divisor) * 100),
            'm13': round((age_distribution['13+'] / divisor) * 100),
            'm16': round((age_distribution['16+'] / divisor) * 100),
            'm18': round((age_distribution['18+'] / divisor) * 100),
        }

    except Exception as e:
        logger.error(f"Error calculating age distribution: {str(e)}")
        return {
            'all': 0, 'm7': 0, 'm13': 0, 'm16': 0, 'm18': 0
        }


# ============================================================================
# Dashboard Context Builder
# ============================================================================

def build_dashboard_context(platform_name):
    """
    Build complete dashboard context with all metrics and chart data.

    This is the main orchestrator function that coordinates all
    analytics data retrieval and formatting.

    Args:
        platform_name (str): Platform identifier.

    Returns:
        dict: Complete context for dashboard template rendering.
    """
    try:
        # Retrieve all metrics
        metrics = get_platform_metrics(platform_name)
        view_trend = calculate_view_trend(platform_name)
        review_trend = calculate_review_trend(platform_name)
        favorite_trend = calculate_favorite_trend(platform_name)
        rating_trend = calculate_rating_trend(platform_name)
        user_trend = calculate_user_trend(platform_name)

        # Retrieve top content
        top_content = get_top_content(platform_name, limit=5)

        # Retrieve chart data
        type_distribution = get_content_type_distribution(platform_name)
        genre_distribution = get_genre_distribution(platform_name, limit=6)
        evolution = get_evolution_data(platform_name)
        age_distribution = get_age_rating_distribution(platform_name)

        logger.info(f"Dashboard context built successfully for {platform_name}")

        return {
            'plataforma': platform_name,
            'metricas': {
                'total_views': view_trend['current'],
                'nota_mitjana': round(metrics['average_rating'], 1),
                'total_ressenyes': metrics['total_reviews'],
                'total_guardados': metrics['total_saved'],
                'usuaris_interessats': metrics['interested_users'],
            },
            'tendencias': {
                'views': view_trend['trend'],
                'users': user_trend['trend'],
                'nota': rating_trend['trend'],
                'ressenyes': review_trend['trend'],
                'guardados': favorite_trend['trend'],
            },
            'top_contingut': top_content,
            'edats_pct': age_distribution,
            'grafic_tipus_data': [type_distribution['movies'], type_distribution['series']],
            'grafic_generes_labels': genre_distribution['labels'],
            'grafic_generes_data': genre_distribution['values'],
            'grafic_evolucio_labels': evolution['labels'],
            'grafic_evolucio_vistes': evolution['views'],
            'grafic_evolucio_usuaris': evolution['users'],
        }

    except Exception as e:
        logger.error(f"Error building dashboard context: {str(e)}")
        raise


class AnalyticsService:
    """
    Facade for analytics domain operations.

    Keeps a clean interface while preserving function-level organization.
    """

    add_view = staticmethod(add_view)
    build_dashboard_context = staticmethod(build_dashboard_context)


__all__ = [
    "AnalyticsService",
    "add_view",
    "build_dashboard_context",
]
