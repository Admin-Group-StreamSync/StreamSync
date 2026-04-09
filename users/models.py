from django.db import models
from django.contrib.auth.models import User


# El teu model actual per a les preferències de l'usuari
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plataformes = models.JSONField(default=list, blank=True)
    generes = models.JSONField(default=list, blank=True)
    idiomes = models.JSONField(default=list, blank=True)
    paisos = models.JSONField(default=list, blank=True)
    edats = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# --- AFEGEIX AIXÒ ARA ---

class Genere(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Pelicula(models.Model):
    titol = models.CharField(max_length=255)
    descripcio = models.TextField(blank=True)
    any = models.IntegerField()
    valoracio = models.FloatField(default=0.0)
    plataforma = models.CharField(max_length=100)  # Ex: 'Disney+', 'Netflix'
    classificacio_edat = models.CharField(max_length=10)  # Ex: '7+', '18'
    imatge = models.ImageField(upload_to='pelicules/', null=True, blank=True)

    # Relació amb gèneres: una peli pot tenir molts gèneres
    generes = models.ManyToManyField(Genere, related_name="pelicules")

    def __str__(self):
        return self.titol