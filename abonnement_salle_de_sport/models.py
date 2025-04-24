from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class AbonnementSalleDeSport(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements_salle')
    date_debut = models.DateField()
    date_fin = models.DateField()
    salle = models.CharField(max_length=255)  # Nom de la salle de sport
    est_actif = models.BooleanField(default=True)  # Si l'abonnement est actif ou non
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abonnement {self.utilisateur.email} à {self.salle} du {self.date_debut} au {self.date_fin}"

class AbonnementEquipement(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements_equipement')
    equipement = models.CharField(max_length=255)  # Nom de l'équipement
    quantite = models.PositiveIntegerField()  # Quantité d'équipement
    est_actif = models.BooleanField(default=True)  # Si l'abonnement est actif ou non
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abonnement équipement {self.utilisateur.email}: {self.equipement} (x{self.quantite})"
