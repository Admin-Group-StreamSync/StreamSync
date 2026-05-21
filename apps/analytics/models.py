from django.contrib.auth.models import User
from django.db import models

from apps.contents.models import Pelicula


# Create your models here.

class Views(models.Model):
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='views')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='views')
    plataforma = models.CharField(max_length=100, blank=True, null=True)
    visualization_date = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)  # Number of times the same user plays the same title.

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['usuari', 'pelicula', 'plataforma'],
                name='unique_view_per_user_content_platform'
            )
        ]
