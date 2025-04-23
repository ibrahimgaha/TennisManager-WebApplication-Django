from datetime import timedelta
from decimal import Decimal
from django.db import models

# Create your models here.
from django.db import models


# Custom User Model
class CustomUser(models.Model):
    phone = models.CharField(max_length=15, blank=True, null=True)
    username = models.CharField(max_length=20,blank=True, null=True )

# Terrain Model
class Terrain(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    terrain = models.ForeignKey(Terrain, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('terrain', 'date', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.user.username} - {self.terrain.name} ({self.date} {self.start_time}-{self.end_time})"

    def calculate_price(self):
        # Convert start and end times to datetime objects to calculate the duration
        start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
        end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)

        # Calculate the duration in hours
        duration = (end - start).seconds / 3600  # Convert seconds to hours

        # If the duration is less than 1 hour, treat it as 1 hour
        if duration < 1:
            duration = 1

        # Calculate the total price based on the duration
        total_price = duration * self.terrain.price_per_hour

        return total_price
    



# Coach Model
class Coach(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    experience_years = models.IntegerField(default=0)

    
# Schedule Model
class Schedule(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.coach.name} - {self.date} ({self.start_time} to {self.end_time})"
    
class ReservationCoach(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="reservations", null=True)  # Fix: Added coach field
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Store computed price

    def save(self, *args, **kwargs):
        duration = (self.end_time.hour + self.end_time.minute / 60) - (self.start_time.hour + self.start_time.minute / 60)
        duration = max(duration, 1)  # Ensure at least 1 hour charge
        self.total_price = Decimal(duration) * self.coach.price_per_hour
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation by {self.user.username} with {self.coach.name} on {self.date} from {self.start_time} to {self.end_time}"