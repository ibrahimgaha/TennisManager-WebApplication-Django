from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class AbonnementTennis(models.Model):
    TYPE_CHOICES = (
        ('hiver', 'Hiver (octobre-juin)'),
        ('ete', 'Été (juillet-août)'),
    )
    TERRAIN_CHOICES = (
        ('terre battue', 'Terre Battue'),
        ('dur', 'Dur'),
    )

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements_tennis')
    type_abonnement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    type_terrain = models.CharField(max_length=20, choices=TERRAIN_CHOICES)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abonnement Tennis {self.utilisateur.email} ({self.type_abonnement}, {self.type_terrain}) du {self.date_debut} au {self.date_fin}"
