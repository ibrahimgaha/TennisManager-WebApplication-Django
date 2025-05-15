from rest_framework import serializers
from .models import AbonnementTennis

class AbonnementTennisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonnementTennis
        fields = ['id', 'utilisateur', 'type_abonnement', 'date_debut', 'date_fin', 'type_terrain', 'est_actif', 'date_creation']
        read_only_fields = ['utilisateur', 'date_creation', 'date_fin']  # Date_fin is being set in view
