from django.urls import path

from reservations.views import add_terrain, check_availability, check_coach_availability, delete_coach_reservation, get_all_coaches, get_terrain_by_id, list_terrains, make_coach_reservation, make_reservation,delete_terrain, update_coach_reservation,update_terrain,getTerrainbyid


urlpatterns = [
    path('terrains/', list_terrains, name='list_terrains'),
    path('terrains/add/', add_terrain, name='add_terrain'),
    path('terrains/<int:terrain_id>/delete/', delete_terrain, name='delete_terrain'),
    path('terrains/<int:terrain_id>/update/', update_terrain, name='update_terrain'),
    path('terrains/<int:terrain_id>/get/', get_terrain_by_id, name='get_terrain_by_id'),
    #path('terrainss/<int:terrain_id>/get/', getTerrainbyid, name='getTerrainbyid'),
    path('reservations/', make_reservation, name='make_reservation'),
    path('reservations/coach/', make_coach_reservation, name='make_coach_reservation'),
    path('reservations/coach/check/<int:coach_id>/<str:date>/<str:start_time>/<str:end_time>/', check_availability, name='check_availability'),
    path('coaches/', get_all_coaches, name='get_all_coaches'),  
    path('coach/<int:coach_id>/availability/', check_coach_availability, name='check_coach_availability'),  
    path('coach/<int:coach_id>/reserve/', make_coach_reservation, name='make_coach_reservation'),

    path('reservations/coach/<int:reservation_id>/delete/', delete_coach_reservation, name='delete_coach_reservation'),
    path('reservations/coach/<int:reservation_id>/update/', update_coach_reservation, name='update_coach_reservation'),

]

