"""
Unit tests for the platform statistics email reporting functionality.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models.models import Profile


@patch.dict('os.environ', {
    'SMTP_HOSTNAME': 'smtp.gmail.com',
    'SMTP_TSL_PORT': '587',
    'SMTP_USER': 'test@gmail.com',
    'SMTP_PASSWORD': 'password123'
})
class AnalyticsEmailTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Create a platform manager user for CinePlus
        self.manager_user = User.objects.create_user(
            username='cineplus_manager',
            email='manager@cineplus.com',
            password='password123'
        )
        self.manager_profile = self.manager_user.profile
        self.manager_profile.manager_de = 'CinePlus'
        self.manager_profile.save()

        # 2. Create another platform manager user for StreamHub
        self.other_manager = User.objects.create_user(
            username='streamhub_manager',
            email='manager@streamhub.com',
            password='password123'
        )
        self.other_profile = self.other_manager.profile
        self.other_profile.manager_de = 'StreamHub'
        self.other_profile.save()

        # 3. Create a normal user (no manager)
        self.normal_user = User.objects.create_user(
            username='normal_user',
            email='user@test.com',
            password='password123'
        )

        self.email_url = reverse('send_dashboard_email', args=['CinePlus'])

    @patch('apps.analytics.views.send_report_email_async')
    @patch('apps.analytics.views.AnalyticsPDFGenerator.generate_dashboard_pdf')
    @patch('apps.analytics.views.AnalyticsService.build_dashboard_context')
    def test_send_email_success(self, mock_build_context, mock_gen_pdf, mock_send_async):
        """Test that a platform manager can successfully trigger the email report."""
        self.client.login(username='cineplus_manager', password='password123')
        
        mock_build_context.return_value = {}
        mock_gen_pdf.return_value = b'fake_pdf_bytes'

        response = self.client.post(
            self.email_url,
            data='{"charts": {}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'ok': True,
            'message': 'El reporte se está enviando a manager@cineplus.com.'
        })
        
        # Verify that send_report_email_async was called with correct parameters
        mock_send_async.assert_called_once()
        args, kwargs = mock_send_async.call_args
        self.assertEqual(args[0], 'CinePlus')
        self.assertEqual(args[1], 'manager@cineplus.com')
        self.assertEqual(args[2], b'fake_pdf_bytes')

    def test_send_email_unauthorized_for_different_platform(self):
        """Test that a manager of a different platform is forbidden from triggering the email report."""
        self.client.login(username='streamhub_manager', password='password123')
        
        response = self.client.post(
            self.email_url,
            data='{"charts": {}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'error': 'Unauthorized access'})

    def test_send_email_unauthorized_for_normal_user(self):
        """Test that a normal user is forbidden from triggering the email report."""
        self.client.login(username='normal_user', password='password123')
        
        response = self.client.post(
            self.email_url,
            data='{"charts": {}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'error': 'Unauthorized access'})

    def test_send_email_no_email_configured(self):
        """Test that if manager user has no email, it returns bad request."""
        # Update manager email to empty
        self.manager_user.email = ''
        self.manager_user.save()
        
        self.client.login(username='cineplus_manager', password='password123')
        
        response = self.client.post(
            self.email_url,
            data='{"charts": {}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {
            'error': 'Su usuario no tiene una dirección de correo electrónico configurada.'
        })

    @patch.dict('os.environ', {}, clear=True)
    def test_send_email_smtp_not_configured(self):
        """Test that if SMTP environment variables are missing, it returns 500 server error."""
        self.client.login(username='cineplus_manager', password='password123')
        
        response = self.client.post(
            self.email_url,
            data='{"charts": {}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('El servidor de correo no está configurado', response.json().get('error', ''))



class SMTPServiceTestCase(TestCase):
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOSTNAME': 'smtp.testserver.com',
        'SMTP_TSL_PORT': '587',
        'SMTP_USER': 'sender@test.com',
        'SMTP_PASSWORD': 'secretpassword'
    })
    def test_send_report_email_smtp_calls(self, mock_smtp_class):
        """Test that send_report_email correctly initializes and uses SMTP with TLS."""
        from apps.analytics.email import send_report_email
        
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance
        
        send_report_email(
            platform_name='CinePlus',
            recipient_email='receiver@test.com',
            pdf_bytes=b'mock_pdf',
            filename='cineplus.pdf'
        )
        
        # Assert SMTP was initialized with the env variables
        mock_smtp_class.assert_called_once_with('smtp.testserver.com', 587, timeout=15)
        
        # Assert starttls was called
        mock_smtp_instance.starttls.assert_called_once()
        
        # Assert login was called with credentials
        mock_smtp_instance.login.assert_called_once_with('sender@test.com', 'secretpassword')
        
        # Assert sendmail was called
        mock_smtp_instance.sendmail.assert_called_once()
        
        # Assert quit was called
        mock_smtp_instance.quit.assert_called_once()
