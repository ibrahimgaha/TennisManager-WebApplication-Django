from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('coach', 'Coach'),
        ('joueur', 'Joueur'),
        ('admin', 'Admin'),
        ('abonnée', 'Abonné'),  # NEW ROLE ADDED HERE

    )

    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    face_encoding = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='joueur')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 
