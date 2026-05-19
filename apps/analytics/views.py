"""
Analytics Views Module.

HTTP request handlers for analytics endpoints.
Handles dashboard rendering and view tracking.
"""
import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from apps.contents.models import Pelicula
from apps.analytics.services import (
    add_view,
    build_dashboard_context
)
from apps.analytics.pdf_service import AnalyticsPDFGenerator

logger = logging.getLogger(__name__)


@login_required
def dashboard_manager(request, plataforma_nom):
    """
    Render analytics dashboard for platform managers.

    This view displays comprehensive analytics metrics and charts
    for a specific platform. Only the platform manager can access.

    Args:
        request: Django HTTP request with authenticated user.
        plataforma_nom (str): Platform identifier.

    Returns:
        HttpResponse: Rendered dashboard template or redirect if unauthorized.
    """
    # Authorization check
    if request.user.profile.manager_de != plataforma_nom:
        messages.error(
            request,
            "You do not have permission to manage this platform."
        )
        logger.warning(
            f"Unauthorized dashboard access attempt by {request.user.username} "
            f"for platform {plataforma_nom}"
        )
        return redirect('pagina_principal')

    try:
        # Build complete dashboard context via service layer
        context = build_dashboard_context(plataforma_nom)

        # Add template rendering fields
        context['pelicules'] = Pelicula.objects.filter(plataforma=plataforma_nom)

        # Convert chart data to JSON for JavaScript
        context['grafic_tipus_data'] = json.dumps(context['grafic_tipus_data'])
        context['grafic_generes_labels'] = json.dumps(context['grafic_generes_labels'])
        context['grafic_generes_data'] = json.dumps(context['grafic_generes_data'])
        context['grafic_evolucio_labels'] = json.dumps(context['grafic_evolucio_labels'])
        context['grafic_evolucio_vistes'] = json.dumps(context['grafic_evolucio_vistes'])
        context['grafic_evolucio_usuaris'] = json.dumps(context['grafic_evolucio_usuaris'])

        logger.info(f"Dashboard accessed by {request.user.username} for {plataforma_nom}")

        return render(request, 'registration/dashboard_manager.html', context)

    except Exception as error:
        logger.error(
            f"Dashboard generation error for platform {plataforma_nom}: {str(error)}"
        )
        messages.error(request, "Error loading dashboard. Please try again later.")
        return redirect('pagina_principal')


@login_required
def register_view(request):
    """
    Register a view/play action for authenticated user.

    API endpoint that increments the view counter for a film.
    Expects JSON POST with film ID.

    Args:
        request: Django HTTP request with authenticated user.

    Returns:
        JsonResponse: Success status with updated count or error message.
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not permitted"},
            status=405
        )

    try:
        # Parse incoming JSON data
        data = json.loads(request.body)
        film_id = data.get("film")

        if not film_id:
            return JsonResponse(
                {"error": "Film ID is missing."},
                status=400
            )

        # Fetch and validate film
        film = get_object_or_404(Pelicula, id=film_id)

        # Register view via service layer
        view_reg, created = add_view(request, film)

        logger.info(
            f"View registered for film {film.titol} "
            f"by user {request.user.username}. Total: {view_reg.count}"
        )

        return JsonResponse({
            "ok": True,
            "count": view_reg.count
        })

    except Pelicula.DoesNotExist:
        logger.warning(f"View registration: Film not found with ID {data.get('film')}")
        return JsonResponse(
            {"error": "Film not found."},
            status=404
        )

    except json.JSONDecodeError:
        logger.error("View registration: Invalid JSON received")
        return JsonResponse(
            {"error": "Invalid JSON format."},
            status=400
        )

    except Exception as error:
        logger.error(f"View registration error: {str(error)}")
        return JsonResponse(
            {"error": str(error)},
            status=500
        )


@login_required
def download_dashboard_pdf(request, plataforma_nom):
    """
    Download analytics dashboard as PDF.

    Generates a comprehensive PDF report with all metrics and charts.
    Accepts JSON POST with base64 encoded chart images.

    Args:
        request: Django HTTP request with authenticated user and JSON body.
        plataforma_nom (str): Platform identifier.

    Returns:
        HttpResponse: PDF file download response.
    """
    # Authorization check
    if request.user.profile.manager_de != plataforma_nom:
        logger.warning(
            f"Unauthorized PDF download attempt by {request.user.username} "
            f"for platform {plataforma_nom}"
        )
        return JsonResponse(
            {"error": "Unauthorized access"},
            status=403
        )

    try:
        # Parse incoming JSON with chart images
        data = json.loads(request.body) if request.body else {}
        chart_images = data.get('charts', {})

        # Build dashboard context
        context = build_dashboard_context(plataforma_nom)

        # Generate PDF
        pdf_bytes = AnalyticsPDFGenerator.generate_dashboard_pdf(
            plataforma_nom,
            context,
            chart_images
        )

        # Prepare response
        filename = (
            f"dashboard_{plataforma_nom}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(
            f"PDF downloaded by {request.user.username} for {plataforma_nom}. "
            f"Filename: {filename}"
        )

        return response

    except json.JSONDecodeError:
        logger.error("PDF download: Invalid JSON received")
        return JsonResponse(
            {"error": "Invalid JSON format"},
            status=400
        )

    except Exception as error:
        logger.error(f"PDF generation error: {str(error)}")
        return JsonResponse(
            {"error": f"PDF generation failed: {str(error)}"},
            status=500
        )

