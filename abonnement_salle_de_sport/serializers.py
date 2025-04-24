from rest_framework import serializers
from .models import AbonnementSalleDeSport, AbonnementEquipement

class AbonnementSalleDeSportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonnementSalleDeSport
        fields = ['id', 'utilisateur', 'date_debut', 'date_fin', 'salle', 'est_actif', 'date_creation']
        read_only_fields = ['utilisateur', 'date_creation']

class AbonnementEquipementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonnementEquipement
        fields = ['id', 'utilisateur', 'equipement', 'quantite', 'est_actif', 'date_creation']
        read_only_fields = ['utilisateur', 'date_creation']
