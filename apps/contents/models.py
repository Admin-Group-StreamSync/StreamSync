from django.db import models

# Create your models here.

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
        choices=[('movie', 'Movie'), ('series', 'Series')],
        default='movie'
    )
    generes = models.ManyToManyField(Genere, related_name="pelicules", blank=True)

    def __str__(self):
        return self.titol

