from django.urls import path
from .views import (
    CoachListView, FaceLoginView, RegisterFaceLoginView, RegisterView, UserProfileView, SubscribeView,
    home_view, login_view, register_view, coach_dashboard_view,
    admin_dashboard_view, joueur_dashboard_view, abonne_dashboard_view, CustomTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', home_view, name='home'),

    # Web-based views (template pages)
    path('login/', login_view, name='login_page'),
    path('register/', register_view, name='register_page'),
    path('coach-dashboard/', coach_dashboard_view, name='coach_dashboard'),
    path('joueur-dashboard/', joueur_dashboard_view, name='joueur_dashboard'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('abonne-dashboard/', abonne_dashboard_view, name='abonne_dashboard'),

    # API endpoints
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='api_login'),
    path('api/profile/', UserProfileView.as_view(), name='api_profile'),
    path('api/subscribe/', SubscribeView.as_view(), name='api_subscribe'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/face-register/', RegisterFaceLoginView.as_view(), name='face-register'),
    path('api/face-login/', FaceLoginView.as_view(), name='face-login'),
    path('api/coaches/', CoachListView.as_view(), name='coach-list'),
]
