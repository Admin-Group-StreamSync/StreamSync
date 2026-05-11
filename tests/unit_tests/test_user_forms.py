from django.test import TestCase
from users.forms import RegistroUsuarioForm
from django.contrib.auth.models import User

class RegistroUsuarioFormTestCase(TestCase):
    def test_valid_form(self):
        """
        Test that the registration form is valid with correct data.
        """
        form_data = {
            'username': 'testuser',
            'first_name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'password2': 'testpassword'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):
        """
        Test that the registration form is invalid if the email is already in use.
        """
        User.objects.create_user(username='existinguser', email='testuser@example.com', password='testpassword')
        form_data = {
            'username': 'testuser',
            'first_name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'password2': 'testpassword'
        }
        form = RegistroUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
