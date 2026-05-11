from typing import Type

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.contents.models import Pelicula

# User: Type[AbstractBaseUser] = get_user_model()

class Profile(models.Model):
    # Stores user preference filters used in recommendations and discovery.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipus = models.JSONField(default=list, blank=True)
    plataformes = models.JSONField(default=list, blank=True)
    generes = models.JSONField(default=list, blank=True)
    edat_rating = models.JSONField(default=list, blank=True)
    manager_de = models.CharField(
        max_length=50,
        choices=[('CinePlus', 'CinePlus'), ('StreamHub', 'StreamHub'), ('PlayMax', 'PlayMax')],
        null=True,
        blank=True
    )
    def __str__(self):
        return f"Profile of {self.user.username}"





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


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


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


class Views(models.Model):
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='views')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='views')
    visualization_date = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)  # Number of times the same user plays the same title.


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
