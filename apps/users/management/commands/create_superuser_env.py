"""
Management command per crear el superuser de Django a partir de variables d'entorn.
Útil per a entorns com Render on no es pot fer python manage.py createsuperuser interactivament.

Variables d'entorn necessàries:
    DJANGO_SUPERUSER_USERNAME  (default: admin)
    DJANGO_SUPERUSER_EMAIL     (default: admin@streamsync.com)
    DJANGO_SUPERUSER_PASSWORD  (OBLIGATORIA)
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superuser a partir de variables d'entorn (segur per a CI/CD i Render)"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@streamsync.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not password:
            self.stderr.write(
                self.style.ERROR(
                    "❌ No s'ha definit DJANGO_SUPERUSER_PASSWORD. "
                    "Afegeix-la com a variable d'entorn a Render."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"⚠️  El superuser '{username}' ja existeix. No s'ha creat de nou.")
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Superuser '{username}' creat correctament.")
        )
