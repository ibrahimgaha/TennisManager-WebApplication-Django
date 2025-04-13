from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  # Pour reconnaissance faciale
    face_encoding = models.TextField(null=True, blank=True)  # Store the encoding here (base64 or any other format)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # on garde username mais email devient identifiant
