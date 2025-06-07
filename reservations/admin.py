from django.contrib import admin
from .models import (
    Coach, ReservationCoach, Schedule, Terrain, Reservation,
    Equipment, EquipmentOrder, Subscription, Tournament,
    TournamentRegistration, Notification, Payment
)

# Register your models here.
admin.site.register(Terrain)
admin.site.register(Reservation)
admin.site.register(Coach)
admin.site.register(Schedule)
admin.site.register(ReservationCoach)
admin.site.register(Equipment)
admin.site.register(EquipmentOrder)
admin.site.register(Subscription)
admin.site.register(Tournament)
admin.site.register(TournamentRegistration)
admin.site.register(Notification)
admin.site.register(Payment)