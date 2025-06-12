from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from reservations.models import Reservation
from reservations.views import create_or_update_schedule, delete_coach, delete_reservation, footer, get_player_coach_reservations, get_user_reservations, home, list_terrains,add_terrain,delete_terrain, reservation, update_reservation,update_terrain,get_terrain_by_id,make_reservation,check_coach_availability,make_coach_reservation,delete_coach_reservation,update_coach_reservation, get_all_coaches,nav
from core.views import RegisterView
from reservations.views import views
from reservations.views import add_coach
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core authentication and dashboard URLs
    path('auth/', include('core.urls')),

    # API URLs
    path('api/', include('abonnement_salle_de_sport.urls')),
    path('api/', include('abonnement_tennis.urls')),

    # Reservations app URLs (includes new API endpoints)
    path('res/', include('reservations.urls')),

    # Match URLs
    path('', include('match.urls')),

    # Terrain management URLs
    path('res/terrains/', list_terrains, name='list_terrains'),
    path('res/terrains/add/', add_terrain, name='add_terrain'),
    path('res/terrains/<int:terrain_id>/delete/', delete_terrain, name='delete_terrain'),
    path('res/terrains/<int:terrain_id>/update/', update_terrain, name='update_terrain'),
    path('res/terrains/<int:terrain_id>/get/', get_terrain_by_id, name='get_terrain_by_id'),

    # Coach management URLs
    path('coaches/', get_all_coaches, name='get_all_coaches'),
    path('coach/<int:coach_id>/availability/<str:date>/', check_coach_availability, name='check_coach_availability'),
    path('coach/<int:coach_id>/reserve/', make_coach_reservation, name='make_coach_reservation'),
    path('reservations/coach/<int:reservation_id>/delete/', delete_coach_reservation, name='delete_coach_reservation'),
    path('reservations/coach/<int:reservation_id>/update/', update_coach_reservation, name='update_coach_reservation'),
    path('coaches/<int:coach_id>/delete/', delete_coach, name='delete_coach'),
    path('add_coach/', add_coach, name='add_coach'),

    # Reservation URLs
    path('reservations/<int:reservation_id>/update/', update_reservation, name='update_reservation'),
    path('reservations/<int:reservation_id>/delete/', delete_reservation, name='delete_reservation'),
    path('reservations/', make_reservation, name='make_reservation'),  # Allow anonymous reservations
    path('my-reservations/', get_user_reservations, name='get_user_reservations'),

    # Schedule management
    path('create-or-update-schedule/', create_or_update_schedule, name='create-or-update-schedule'),
    path('player/reservations/', get_player_coach_reservations, name='get_player_coach_reservations'),

    # User registration
    path('register/', RegisterView.as_view(), name='register'),

    # Template views
    path('navbar/', nav, name='navbar'),
    path('footer/', footer, name='footer'),

    # Pages
    path('reservation', reservation, name='reservation'),

    # Home page
    path('', home, name='home'),
]


# Serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)