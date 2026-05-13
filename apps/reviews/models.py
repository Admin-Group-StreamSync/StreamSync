from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.contents.models import Pelicula


# Create your models here.


class Ressenya(models.Model):
    # User review with numeric score and optional comment.
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ressenyes')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='ressenyes')
    puntuacio = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    comentari = models.TextField(blank=True, null=True)
    data_publicacio = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuari', 'pelicula')

    def __str__(self):
        return f"{self.usuari.username} - {self.pelicula.titol} ({self.puntuacio}/10)"

class Feedback(models.Model):
    # Feedback submitted from the app (rating, issue reports, suggestions).
    TIPUS_CHOICES = [
        ('general', 'General rating'),
        ('error', 'Report error'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other comments'),
    ]

    titol = models.CharField(max_length=200)
    descripcio = models.TextField()
    tipus = models.CharField(max_length=20, choices=TIPUS_CHOICES)
    rating = models.IntegerField(null=True, blank=True)

    data_creacio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipus} - {self.titol}"