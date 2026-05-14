from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.contents.models import Pelicula

User  = get_user_model()
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



@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)






