from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipus = models.JSONField(default=list, blank=True)
    plataformes = models.JSONField(default=list, blank=True)
    generes = models.JSONField(default=list, blank=True)
    edat_rating = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Genere(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class Pelicula(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    titol = models.CharField(max_length=255)
    director = models.CharField(max_length=255, blank=True, null=True)
    sinopsi = models.TextField(blank=True, null=True)
    any = models.IntegerField(null=True, blank=True)
    valoracio = models.FloatField(default=0.0)
    plataforma = models.CharField(max_length=100, blank=True, null=True)
    classificacio_edat = models.CharField(max_length=50, blank=True, null=True)
    durada = models.CharField(max_length=50, blank=True, null=True)
    imatge = models.URLField(max_length=500, null=True, blank=True)
    tipus = models.CharField(
        max_length=20,
        choices=[('movie', 'Pel·lícula'), ('series', 'Sèrie')],
        default='movie'
    )
    generes = models.ManyToManyField(Genere, related_name="pelicules", blank=True)

    def __str__(self):
        return self.titol


class Carpeta(models.Model):
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='les_meves_carpetes')
    nom = models.CharField(max_length=100)
    icona = models.CharField(max_length=50, default="bi-star-fill")
    color = models.CharField(max_length=20, default="#8a2be2")
    data_creacio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Carpeta"
        verbose_name_plural = "Carpetes"

    def __str__(self):
        return f"{self.nom} ({self.usuari.username})"


class LlistaPersonal(models.Model):
    usuari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='la_meva_llista')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='elements', null=True, blank=True)
    data_afegida = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuari', 'pelicula', 'carpeta')
        verbose_name = "Element de llista"
        verbose_name_plural = "Elements de llistes"


# ✅ SIGNAL CORREGIT — eliminat el bloc 'else' que sobreescrivia el perfil
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


class Ressenya(models.Model):
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