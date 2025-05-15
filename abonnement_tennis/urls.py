from django.urls import path
from .views import AbonnementTennisCreateView, AbonnementTennisListView, AbonnementTennisDetailView

urlpatterns = [
    # Créer un abonnement tennis
    path('abonnement/tennis/', AbonnementTennisCreateView.as_view(), name='abonnement-tennis'),
    
    # Liste des abonnements (accessible seulement pour les administrateurs)
    path('abonnements/', AbonnementTennisListView.as_view(), name='abonnements-list'),
    
    # Détails, mise à jour et suppression d'un abonnement spécifique
    path('abonnements/<int:pk>/', AbonnementTennisDetailView.as_view(), name='abonnement-detail'),
]
