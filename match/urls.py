from django.urls import path
from .views import MatchListCreateView, JoinMatchView, find_matches_by_user

urlpatterns = [
    
    # ✅ 1. Create or List Matches
    # URL: http://localhost:8000/matches/
    path('matches/', MatchListCreateView.as_view(), name='match-list-create'),

    # 2. Join a Match
    # URL format: http://localhost:8000/matches/<id>/join/
    path('matches/<int:pk>/join/', JoinMatchView.as_view(), name='match-join'),

    # ✅ 3. Search Matches by User
    # URL format: http://localhost:8000/matches/search/?q=<username-or-email>
    path('matches/search/', find_matches_by_user, name='match-search'),
]















