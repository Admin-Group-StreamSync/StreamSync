"""
Analytics PDF Service Module.

Service for generating PDF reports with WeasyPrint.
Handles PDF generation with metrics, charts, and data visualization.
"""
import base64
import logging
from datetime import datetime

from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from io import BytesIO

logger = logging.getLogger(__name__)


class AnalyticsPDFGenerator:
    """Generate PDF reports for analytics dashboards."""

    @staticmethod
    def generate_dashboard_pdf(platform_name, context, chart_images=None):
        """
        Generate a PDF report from dashboard context and chart images.

        This method creates a professional PDF document containing:
        - Metrics and KPIs
        - Chart data visualizations
        - Age rating distribution
        - Top content ranking

        Args:
            platform_name (str): Platform identifier.
            context (dict): Dashboard context from services.build_dashboard_context().
            chart_images (dict): Optional dict with base64 encoded chart images:
                {
                    'grafic_tipus_data': 'data:image/png;base64,...',
                    'grafic_generes': 'data:image/png;base64,...',
                    'grafic_evolucio': 'data:image/png;base64,...',
                    'grafic_edats': 'data:image/png;base64,...'
                }

        Returns:
            bytes: PDF file content as bytes.

        Raises:
            Exception: If PDF generation fails.
        """
        try:
            # Prepare enhanced context with images
            pdf_context = AnalyticsPDFGenerator._prepare_context(
                platform_name,
                context,
                chart_images or {}
            )

            # Render HTML template
            html_string = render_to_string(
                'registration/dashboard_pdf.html',
                pdf_context
            )

            # Convert HTML to PDF
            pdf_bytes = AnalyticsPDFGenerator._html_to_pdf(html_string)

            logger.info(
                f"PDF generated successfully for platform {platform_name}. "
                f"Size: {len(pdf_bytes) / 1024:.2f}KB"
            )

            return pdf_bytes

        except Exception as error:
            logger.error(f"PDF generation error for {platform_name}: {str(error)}")
            raise

    @staticmethod
    def _prepare_context(platform_name, context, chart_images):
        """
        Prepare and enhance context for PDF rendering.

        Args:
            platform_name (str): Platform identifier.
            context (dict): Dashboard context.
            chart_images (dict): Chart images as base64.

        Returns:
            dict: Enhanced context with PDF-specific data.
        """
        # Add generation metadata
        context['generation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        context['platform_name'] = platform_name

        # Add chart images
        context['chart_images'] = chart_images

        # Add page styling for PDF
        context['is_pdf'] = True

        # Format metrics for PDF display
        context['formatted_metrics'] = {
            'total_views': f"{context['metricas']['total_views']:,}",
            'total_reviews': f"{context['metricas']['total_ressenyes']:,}",
            'total_saved': f"{context['metricas']['total_guardados']:,}",
            'interested_users': f"{context['metricas']['usuaris_interessats']:,}",
            'average_rating': f"{context['metricas']['nota_mitjana']:.1f}/10",
        }

        # Format trends
        context['formatted_trends'] = {
            'views': f"{context['tendencias']['views']:+.1f}%",
            'users': f"{context['tendencias']['users']:+.1f}%",
            'rating': f"{context['tendencias']['nota']:+.1f}",
            'reviews': f"{context['tendencias']['ressenyes']:+.1f}%",
            'saved': f"{context['tendencias']['guardados']:+.1f}%",
        }

        # Get trend indicators (up/down)
        context['trend_indicators'] = {
            'views': 'up' if context['tendencias']['views'] > 0 else 'down',
            'users': 'up' if context['tendencias']['users'] > 0 else 'down',
            'rating': 'up' if context['tendencias']['nota'] > 0 else 'down',
            'reviews': 'up' if context['tendencias']['ressenyes'] > 0 else 'down',
            'saved': 'up' if context['tendencias']['guardados'] > 0 else 'down',
        }

        return context

    @staticmethod
    def _html_to_pdf(html_string):
        """
        Convert HTML string to PDF bytes using WeasyPrint.

        Args:
            html_string (str): HTML content as string.

        Returns:
            bytes: PDF file content.
        """
        try:
            # Create HTML object
            html_object = HTML(string=html_string, base_url='/')

            # Define CSS for PDF styling
            css_list = [
                CSS(string=AnalyticsPDFGenerator._get_pdf_css())
            ]

            # Generate PDF
            pdf_buffer = BytesIO()
            html_object.write_pdf(pdf_buffer, stylesheets=css_list)

            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()

        except Exception as error:
            logger.error(f"HTML to PDF conversion error: {str(error)}")
            raise

    @staticmethod
    def _get_pdf_css():
        """
        Get CSS styles optimized for PDF rendering.

        Returns:
            str: CSS stylesheet as string.
        """
        return """
        @page {
            size: A4;
            margin: 1cm;
        }

        @font-face {
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        * {
            font-family: 'Segoe UI', Arial, sans-serif;
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            color: #1e293b;
            font-size: 10pt;
            line-height: 1.6;
        }

        /* Header */
        .pdf-header {
            background-color: #3b5bdb;
            color: white;
            padding: 20px;
            margin: -1cm -1cm 20px -1cm;
            text-align: center;
            border-bottom: 3px solid #1e40af;
        }

        .pdf-header h1 {
            font-size: 24pt;
            margin: 0 0 5px 0;
            font-weight: 700;
        }

        .pdf-header p {
            font-size: 10pt;
            margin: 0;
            opacity: 0.9;
        }

        .pdf-meta {
            font-size: 8pt;
            margin: 0;
            opacity: 0.8;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }

        .metric-card {
            background: #f8f9fa;
            border: 1px solid #e2e8f0;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            page-break-inside: avoid;
        }

        .metric-label {
            font-size: 8pt;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 16pt;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 3px;
        }

        .metric-trend {
            font-size: 8pt;
            font-weight: 600;
        }

        .trend-up {
            color: #16a34a;
        }

        .trend-down {
            color: #dc2626;
        }

        /* Charts */
        .charts-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }

        .chart-container {
            background: white;
            border: 1px solid #e2e8f0;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }

        .chart-container h3 {
            font-size: 12pt;
            margin: 0 0 10px 0;
            color: #1e293b;
            font-weight: 600;
        }

        .chart-image {
            max-width: 100%;
            height: auto;
            display: block;
        }

        /* Age Distribution */
        .age-section {
            page-break-inside: avoid;
            margin-bottom: 20px;
        }

        .age-section h3 {
            font-size: 12pt;
            margin: 0 0 10px 0;
            color: #1e293b;
            font-weight: 600;
        }

        .age-bar-item {
            display: grid;
            grid-template-columns: 80px 1fr 40px;
            gap: 8px;
            align-items: center;
            margin-bottom: 8px;
        }

        .age-label {
            font-size: 9pt;
            font-weight: 600;
            color: #334155;
        }

        .age-bar {
            height: 16px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
        }

        .age-fill {
            height: 100%;
            background: linear-gradient(90deg, #a855f7, #ec4899);
        }

        .age-percentage {
            font-size: 9pt;
            font-weight: 600;
            color: #334155;
            text-align: right;
        }

        /* Top Content */
        .top-content-section {
            page-break-inside: avoid;
            margin-bottom: 20px;
        }

        .top-content-section h3 {
            font-size: 12pt;
            margin: 0 0 10px 0;
            color: #1e293b;
            font-weight: 600;
        }

        .content-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .content-item {
            display: grid;
            grid-template-columns: 45px 1fr 60px;
            gap: 10px;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 9pt;
        }

        .content-rank {
            font-weight: 700;
            color: #a855f7;
            font-size: 12pt;
        }

        .content-title {
            font-weight: 600;
            color: #1e293b;
        }

        .content-views {
            text-align: right;
            color: #64748b;
            font-weight: 600;
        }

        /* Footer */
        .pdf-footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
            font-size: 8pt;
            color: #94a3b8;
            text-align: center;
            page-break-inside: avoid;
        }

        /* Page breaks */
        .page-break {
            page-break-after: always;
        }

        /* Table-like sections */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }

        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            font-size: 9pt;
        }

        th {
            background: #f1f5f9;
            font-weight: 600;
            color: #334155;
        }

        /* Utilities */
        .text-center {
            text-align: center;
        }

        .mt-20 {
            margin-top: 20px;
        }

        .mb-20 {
            margin-bottom: 20px;
        }

        .section-divider {
            height: 2px;
            background: linear-gradient(90deg, #a855f7, #ec4899);
            margin: 20px 0;
            page-break-inside: avoid;
        }
        """

