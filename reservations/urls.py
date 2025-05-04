from django.urls import path

from reservations.views import add_coach, add_terrain, check_availability, check_coach_availability, create_or_update_schedule, delete_coach, delete_coach_reservation, delete_reservation, get_all_coaches, get_player_coach_reservations, get_terrain_by_id, get_user_reservations, list_terrains, make_coach_reservation, make_reservation,delete_terrain, update_coach_reservation, update_reservation,update_terrain,getTerrainbyid
from core.views import RegisterView

urlpatterns = [
    path('terrains/', list_terrains, name='list_terrains'),
    path('terrains/add/', add_terrain, name='add_terrain'),
    path('terrains/<int:terrain_id>/delete/', delete_terrain, name='delete_terrain'),
    path('terrains/<int:terrain_id>/update/', update_terrain, name='update_terrain'),
    path('terrains/<int:terrain_id>/get/', get_terrain_by_id, name='get_terrain_by_id'),
    #path('terrainss/<int:terrain_id>/get/', getTerrainbyid, name='getTerrainbyid'),
    path('reservations/', make_reservation, name='make_reservation'),
   
    path('reservations/coach/check/<int:coach_id>/<str:date>/<str:start_time>/<str:end_time>/', check_availability, name='check_availability'),
    path('coaches/', get_all_coaches, name='get_all_coaches'),  
    path('coach/<int:coach_id>/availability/', check_coach_availability, name='check_coach_availability'),  
    path('coach/<int:coach_id>/reserve/', make_coach_reservation, name='make_coach_reservation'),
    path('add_coach/',add_coach, name='add_coach'),
    path('reservations/coach/<int:reservation_id>/delete/', delete_coach_reservation, name='delete_coach_reservation'),
    path('reservations/coach/<int:reservation_id>/update/', update_coach_reservation, name='update_coach_reservation'),
    path('register/', RegisterView.as_view(), name='register'),
    path('coaches/<int:coach_id>/delete/', delete_coach, name='delete_coach'),
    path('reservations/<int:reservation_id>/update/', update_reservation, name='update_reservation'),
    path('reservations/<int:reservation_id>/delete/', delete_reservation, name='delete_reservation'),
        path('reservations/', get_user_reservations, name='get_user_reservations'),
 path('create-or-update-schedule/', create_or_update_schedule, name='create-or-update-schedule'),
     path('player/reservations/', get_player_coach_reservations, name='get_player_coach_reservations'),


    

]

