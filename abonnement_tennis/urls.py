from django.urls import path
from .views import AbonnementTennisCreateView

urlpatterns = [
    path('abonnement/tennis/', AbonnementTennisCreateView.as_view(), name='abonnement-tennis'),
]
