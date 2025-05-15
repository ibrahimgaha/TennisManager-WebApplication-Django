from django.urls import path
from .views import AbonnementEquipementCreateView, EquipementChoicesView

urlpatterns = [
    # Vue pour créer un abonnement à un équipement
    path('abonnement-equipement/', AbonnementEquipementCreateView.as_view(), name='abonnement-equipement-create'),

    # Vue pour récupérer les choix d'équipement
    path('equipement-choices/', EquipementChoicesView.as_view(), name='equipement-choices'),
]
