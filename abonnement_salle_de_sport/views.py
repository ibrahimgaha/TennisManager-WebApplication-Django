from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AbonnementEquipement
from .serializers import AbonnementEquipementSerializer

# Vue pour créer une commande d'équipement
class AbonnementEquipementCreateView(generics.CreateAPIView):
    queryset = AbonnementEquipement.objects.all()
    serializer_class = AbonnementEquipementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # L'utilisateur connecté est automatiquement lié à la commande
        serializer.save(utilisateur=self.request.user)

# Vue pour récupérer les choix disponibles pour l'équipement (utile pour le frontend)
class EquipementChoicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Retourne les choix d'équipements sous forme de liste
        choices = [{'value': c[0], 'label': c[1]} for c in AbonnementEquipement.EQUIPEMENT_CHOICES]
        return Response(choices)
