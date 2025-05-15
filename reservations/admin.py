from django.contrib import admin

from .models import Coach, ReservationCoach, Schedule, Terrain,Reservation


# Register your models here.

admin.site.register(Terrain)
admin.site.register(Reservation)

admin.site.register(Coach)
admin.site.register(Schedule)
admin.site.register(ReservationCoach)