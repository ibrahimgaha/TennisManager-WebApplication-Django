from rest_framework import generics, permissions
from .models import AbonnementSalleDeSport, AbonnementEquipement
from .serializers import AbonnementSalleDeSportSerializer, AbonnementEquipementSerializer

# Vue pour créer un abonnement à la salle de sport
class AbonnementSalleDeSportCreateView(generics.CreateAPIView):
    queryset = AbonnementSalleDeSport.objects.all()
    serializer_class = AbonnementSalleDeSportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

# Vue pour créer un abonnement à un équipement
class AbonnementEquipementCreateView(generics.CreateAPIView):
    queryset = AbonnementEquipement.objects.all()
    serializer_class = AbonnementEquipementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)
