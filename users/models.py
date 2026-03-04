from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Users(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)


