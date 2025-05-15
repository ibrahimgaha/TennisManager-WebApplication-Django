from rest_framework import generics, permissions, response, status
from .models import AbonnementTennis
from .serializers import AbonnementTennisSerializer
from dateutil.relativedelta import relativedelta

class AbonnementTennisCreateView(generics.CreateAPIView):
    queryset = AbonnementTennis.objects.all()
    serializer_class = AbonnementTennisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        type_abonnement = serializer.validated_data['type_abonnement']
        date_debut = serializer.validated_data['date_debut']

        if type_abonnement == "ete":
            if date_debut.month < 7:
                date_debut = date_debut.replace(month=7, day=1)
            date_fin = date_debut + relativedelta(months=2)

        elif type_abonnement == "hiver":
            if date_debut.month < 10:
                date_debut = date_debut.replace(month=10, day=1)
            date_fin = date_debut + relativedelta(months=9)

        abonnement = serializer.save(utilisateur=user, date_debut=date_debut, date_fin=date_fin)

        if user.role == 'joueur':
            user.role = 'abonnée'
            user.save()

        self.abonnement_created = abonnement

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        user_role = self.request.user.role
        return response.Response(
            {
                'message': 'Abonnement tennis créé avec succès.',
                'abonnement': AbonnementTennisSerializer(self.abonnement_created).data,
                'nouveau_role_utilisateur': user_role
            },
            status=status.HTTP_201_CREATED
        )


class AbonnementTennisListView(generics.ListAPIView):
    queryset = AbonnementTennis.objects.all()
    serializer_class = AbonnementTennisSerializer
    permission_classes = [permissions.IsAdminUser]


class AbonnementTennisDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AbonnementTennis.objects.all()
    serializer_class = AbonnementTennisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if self.request.user.is_staff or obj.utilisateur == self.request.user:
            return obj
        else:
            raise permissions.PermissionDenied("Vous n'avez pas la permission d'accéder à cet abonnement.")

    def update(self, request, *args, **kwargs):
        abonnement = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(abonnement, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        type_abonnement = serializer.validated_data.get('type_abonnement', abonnement.type_abonnement)
        date_debut = serializer.validated_data.get('date_debut', abonnement.date_debut)

        if type_abonnement == "ete":
            if date_debut.month < 7:
                date_debut = date_debut.replace(month=7, day=1)
            date_fin = date_debut + relativedelta(months=2)

        elif type_abonnement == "hiver":
            if date_debut.month < 10:
                date_debut = date_debut.replace(month=10, day=1)
            date_fin = date_debut + relativedelta(months=9)
        else:
            date_fin = abonnement.date_fin  # On garde la date_fin actuelle

        serializer.save(date_debut=date_debut, date_fin=date_fin)

        return response.Response(
            {
                'message': 'Abonnement tennis mis à jour avec succès.',
                'abonnement': AbonnementTennisSerializer(abonnement).data
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        abonnement = self.get_object()
        self.perform_destroy(abonnement)
        return response.Response(
            {"detail": "Abonnement supprimé avec succès."},
            status=status.HTTP_200_OK
        )
