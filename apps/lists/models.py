from django.contrib.auth.models import User
from django.db import models

from apps.users.models.models import Pelicula


# Create your models here.

class Carpeta(models.Model):
    # User-owned folder to organize saved titles.
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='les_meves_carpetes')
    nom = models.CharField(max_length=100)
    icona = models.CharField(max_length=50, default="bi-star-fill")
    color = models.CharField(max_length=20, default="#8a2be2")
    data_creacio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Folder"
        verbose_name_plural = "Folders"

    def __str__(self):
        return f"{self.nom} ({self.usuari.username})"


class LlistaPersonal(models.Model):
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='la_meva_llista')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='elements', null=True, blank=True)
    data_afegida = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuari', 'pelicula', 'carpeta')
        verbose_name = "List item"
        verbose_name_plural = "List items"

