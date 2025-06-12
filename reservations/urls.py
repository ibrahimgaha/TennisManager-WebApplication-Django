from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from reservations.views import (
    add_coach, add_terrain, check_coach_availability, create_or_update_schedule,
    delete_coach, delete_coach_reservation, delete_reservation, get_all_coaches,
    get_player_coach_reservations, get_terrain_by_id, get_user_reservations,
    list_terrains, make_coach_reservation, make_reservation, delete_terrain,
    update_coach_reservation, update_reservation, update_terrain, nav,
    footer, home, reservation
)
from reservations.api_views import (
    terrain_management, terrain_detail, court_reservations, cancel_reservation,
    equipment_list, order_equipment, user_orders, tournament_list, register_tournament,
    dashboard_stats, user_list, update_user_role, delete_user, user_notifications,
    mark_notification_read, coach_schedule, delete_schedule, user_payments,
    create_payment, add_equipment, equipment_detail, admin_coach_schedule_management,
    coach_availability, book_coach_slot, book_coach_session, user_subscriptions, cancel_subscription,
    subscription_plans, player_reservations, player_upcoming_reservations, coaches_list,
    update_court_reservation, cancel_coach_reservation, update_coach_reservation,
    update_coach, get_coach_details, create_coach_schedule, get_coach_schedule, delete_schedule_slot,
    get_recent_activities, get_todays_coach_schedules, get_user_weekly_spending,
    get_coach_reservations, get_coach_dashboard_stats
)
from core.views import RegisterView

urlpatterns = [
    # Terrain management URLs
    path('terrains/', list_terrains, name='list_terrains'),
    path('terrains/add/', add_terrain, name='add_terrain'),
    path('terrains/<int:terrain_id>/delete/', delete_terrain, name='delete_terrain'),
    path('terrains/<int:terrain_id>/update/', update_terrain, name='update_terrain'),
    path('terrains/<int:terrain_id>/get/', get_terrain_by_id, name='get_terrain_by_id'),

    # Reservation URLs
    path('reservations/', make_reservation, name='make_reservation'),
    path('reservations/<int:reservation_id>/update/', update_reservation, name='update_reservation'),
    path('reservations/<int:reservation_id>/delete/', delete_reservation, name='delete_reservation'),
    path('user-reservations/', get_user_reservations, name='get_user_reservations'),

    # Coach management URLs
    path('coaches/', get_all_coaches, name='get_all_coaches'),
    path('coach/<int:coach_id>/availability/<str:date>/', check_coach_availability, name='check_coach_availability'),
    path('coach/<int:coach_id>/reserve/', make_coach_reservation, name='make_coach_reservation'),
    path('coaches/<int:coach_id>/delete/', delete_coach, name='delete_coach'),
    path('add_coach/', add_coach, name='add_coach'),

    # Coach reservation URLs
    path('reservations/coach/<int:reservation_id>/delete/', delete_coach_reservation, name='delete_coach_reservation'),
    path('reservations/coach/<int:reservation_id>/update/', update_coach_reservation, name='update_coach_reservation'),

    # Schedule management
    path('create-or-update-schedule/', create_or_update_schedule, name='create-or-update-schedule'),
    path('player/reservations/', get_player_coach_reservations, name='get_player_coach_reservations'),

    # User registration
    path('register/', RegisterView.as_view(), name='register'),

    # Navigation
    path('navbar/', nav, name='navbar'),

    # API endpoints
    path('api/terrains/', terrain_management, name='terrain_management'),
    path('api/terrains/<int:terrain_id>/', terrain_detail, name='terrain_detail'),
    path('api/court-reservations/', court_reservations, name='court_reservations'),
    path('api/reservations/<int:reservation_id>/cancel/', cancel_reservation, name='cancel_reservation'),
    path('api/court-reservations/<int:reservation_id>/update/', update_court_reservation, name='update_court_reservation'),

    # Coach reservation management
    path('api/coach-reservations/<int:reservation_id>/cancel/', cancel_coach_reservation, name='cancel_coach_reservation'),
    path('api/coach-reservations/<int:reservation_id>/update/', update_coach_reservation, name='update_coach_reservation'),

    # Coach management (admin)
    path('api/coaches/<int:coach_id>/details/', get_coach_details, name='get_coach_details'),
    path('api/coaches/<int:coach_id>/update/', update_coach, name='update_coach'),

    # Coach schedule management (admin)
    path('api/coach-schedule/create/', create_coach_schedule, name='create_coach_schedule'),
    path('api/coaches/<int:coach_id>/schedule/', get_coach_schedule, name='get_coach_schedule'),
    path('api/schedule-slots/<int:slot_id>/delete/', delete_schedule_slot, name='delete_schedule_slot'),

    # Admin dashboard
    path('api/admin/recent-activities/', get_recent_activities, name='get_recent_activities'),

    # Player dashboard
    path('api/player/todays-coach-schedules/', get_todays_coach_schedules, name='get_todays_coach_schedules'),
    path('api/player/weekly-spending/', get_user_weekly_spending, name='get_user_weekly_spending'),

    # Coach dashboard
    path('api/coach/reservations/', get_coach_reservations, name='get_coach_reservations'),
    path('api/coach/dashboard-stats/', get_coach_dashboard_stats, name='get_coach_dashboard_stats'),

    path('api/equipment/', equipment_list, name='equipment_list'),
    path('api/equipment/order/', order_equipment, name='order_equipment'),
    path('api/equipment/orders/', user_orders, name='user_orders'),
    path('api/equipment/add/', add_equipment, name='add_equipment'),
    path('api/equipment/<int:equipment_id>/', equipment_detail, name='equipment_detail'),

    path('api/tournaments/', tournament_list, name='tournament_list'),
    path('api/tournaments/<int:tournament_id>/register/', register_tournament, name='register_tournament'),

    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('api/users/', user_list, name='user_list'),
    path('api/users/<int:user_id>/role/', update_user_role, name='update_user_role'),
    path('api/users/<int:user_id>/delete/', delete_user, name='delete_user'),

    path('api/notifications/', user_notifications, name='user_notifications'),
    path('api/notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),

    path('api/coach/schedule/', coach_schedule, name='coach_schedule'),
    path('api/coach/schedule/<int:schedule_id>/delete/', delete_schedule, name='delete_schedule'),

    # Admin schedule management
    path('api/admin/coach-schedules/', admin_coach_schedule_management, name='admin_coach_schedule_management'),

    # Coach management
    path('api/coaches/', coaches_list, name='coaches_list'),

    # Coach availability and booking
    path('api/coach/<int:coach_id>/availability/', coach_availability, name='coach_availability'),
    path('api/coach/book-slot/', book_coach_session, name='book_coach_slot'),  # Use new function
    path('api/coach/book-session/', book_coach_session, name='book_coach_session'),  # Alternative URL

    path('api/payments/', user_payments, name='user_payments'),
    path('api/payments/create/', create_payment, name='create_payment'),

    # Subscription endpoints
    path('api/subscriptions/', user_subscriptions, name='user_subscriptions'),
    path('api/subscriptions/cancel/', cancel_subscription, name='cancel_subscription'),
    path('api/subscriptions/plans/', subscription_plans, name='subscription_plans'),

    # Player reservation endpoints
    path('api/player/reservations/', player_reservations, name='player_reservations'),
    path('api/player/upcoming-reservations/', player_upcoming_reservations, name='player_upcoming_reservations'),
]

# Serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
