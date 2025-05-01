from rest_framework import generics, permissions, response, status
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import AbonnementTennis
from .serializers import AbonnementTennisSerializer

class AbonnementTennisCreateView(generics.CreateAPIView):
    queryset = AbonnementTennis.objects.all()
    serializer_class = AbonnementTennisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        type_abonnement = serializer.validated_data['type_abonnement']
        date_debut = serializer.validated_data['date_debut']

        # Ajustement automatique pour l'abonnement "été"
        if type_abonnement == "ete":
            # Si la date de début est avant juillet, ajuster au 1er juillet
            if date_debut.month < 7:
                date_debut = date_debut.replace(month=7, day=1)
            # Calcul de la date de fin : 2 mois après la date de début
            date_fin = date_debut + relativedelta(months=2)

        # Ajustement automatique pour l'abonnement "hiver"
        elif type_abonnement == "hiver":
            # Si la date de début est avant octobre, ajuster au 1er octobre
            if date_debut.month < 10:
                date_debut = date_debut.replace(month=10, day=1)
            # Calcul de la date de fin : 9 mois après la date de début
            date_fin = date_debut + relativedelta(months=9)

        # Sauvegarde de l'abonnement
        abonnement = serializer.save(utilisateur=user, date_debut=date_debut, date_fin=date_fin)

        # Si l'utilisateur est joueur, on le passe à abonné
        if user.role == 'joueur':
            user.role = 'abonnée'
            user.save()

        self.abonnement_created = abonnement

    def create(self, request, *args, **kwargs):
        response_obj = super().create(request, *args, **kwargs)
        user_role = self.request.user.role
        return response.Response(
            {
                'message': 'Abonnement tennis créé avec succès.',
                'abonnement': AbonnementTennisSerializer(self.abonnement_created).data,
                'nouveau_role_utilisateur': user_role
            },
            status=status.HTTP_201_CREATED
        )
