from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class AbonnementEquipement(models.Model):
    EQUIPEMENT_CHOICES = [
        ('RAQUETTE', 'Raquette'),
        ('SAC', 'Sac'),
        ('BALLE', 'Balle'),
        ('CHAUSSURE', 'Chaussure'),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements_equipement')
    equipement = models.CharField(max_length=20, choices=EQUIPEMENT_CHOICES)
    quantite = models.PositiveIntegerField()
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande {self.equipement} (x{self.quantite}) par {self.utilisateur.email}"
