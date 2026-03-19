from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plataformes = models.JSONField(default=list, blank=True)
    generes = models.JSONField(default=list, blank=True)
    idiomes = models.JSONField(default=list, blank=True)
    paisos = models.JSONField(default=list, blank=True)
    edats = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"