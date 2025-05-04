from django.urls import path
from .views import CoachListView, FaceLoginView, RegisterFaceLoginView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('face-register/', RegisterFaceLoginView.as_view(), name='face-register'),
    path('face-login/', FaceLoginView.as_view(), name='face-login'),
    path('coaches/', CoachListView.as_view(), name='coach-list'),

]
