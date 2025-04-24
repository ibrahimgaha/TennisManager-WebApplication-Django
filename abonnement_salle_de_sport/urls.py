from django.urls import path
from .views import AbonnementSalleDeSportCreateView, AbonnementEquipementCreateView

urlpatterns = [
    path('salle/', AbonnementSalleDeSportCreateView.as_view(), name='abonnement-salle-create'),
    path('equipement/', AbonnementEquipementCreateView.as_view(), name='abonnement-equipement-create'),
]
