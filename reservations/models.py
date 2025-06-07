from datetime import timedelta
from decimal import Decimal
from django.db import models

# Create your models here.
from django.db import models
from core.models import User

# Terrain Model
class Terrain(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    terrain = models.ForeignKey(Terrain, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('terrain', 'date', 'start_time', 'end_time')

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} - {self.terrain.name} ({self.date} {self.start_time}-{self.end_time})"

    def calculate_price(self):
        start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
        end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)

     
        duration = (end - start).seconds / 3600  

      
        if duration < 1:
            duration = 1

        total_price = duration * self.terrain.price_per_hour

        return total_price
    



class Coach(models.Model):
    name = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    experience = models.IntegerField(null=True)  # Allow experience to be null

    class Meta:
        db_table = 'coach'
    def __str__(self):
        return self.name




    
class ReservationCoach(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)  # This should be directly referencing Coach
    date = models.DateField(default=False)
    start_time = models.TimeField(default=False)
    end_time = models.TimeField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'reservations_coach'  # Keep this name

    def save(self, *args, **kwargs):
        duration = (self.end_time.hour + self.end_time.minute / 60) - (self.start_time.hour + self.start_time.minute / 60)
        duration = max(duration, 1)
        self.total_price = Decimal(duration) * self.coach.price_per_hour
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation by {self.user.username} with {self.coach.name} on {self.date}"


class Schedule(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="schedules")  # Same here, directly reference Coach

    date = models.DateField(default=False)
    start_time = models.TimeField(default=False)
    end_time = models.TimeField(default=False)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.coach.name} - {self.date} ({self.start_time} to {self.end_time})"

    class Meta:
        db_table = 'reservations_coach_model'  # Optional, based on your needs
