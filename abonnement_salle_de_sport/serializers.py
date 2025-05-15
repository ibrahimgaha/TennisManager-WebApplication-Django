from rest_framework import serializers
from .models import AbonnementEquipement

class AbonnementEquipementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonnementEquipement
        fields = ['id', 'utilisateur', 'equipement', 'quantite', 'est_actif', 'date_creation']
        read_only_fields = ['utilisateur', 'date_creation']
