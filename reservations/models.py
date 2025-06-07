from datetime import timedelta, datetime
from decimal import Decimal
from django.db import models
from django.utils import timezone
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    terrain = models.ForeignKey(Terrain, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('terrain', 'date', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.user.username} - {self.terrain.name} ({self.date} {self.start_time}-{self.end_time})"

    def calculate_price(self):
        """Calculate the total price for the reservation"""
        # Handle both time objects and string inputs
        if isinstance(self.start_time, str):
            start_time = datetime.strptime(self.start_time, '%H:%M').time()
        else:
            start_time = self.start_time

        if isinstance(self.end_time, str):
            end_time = datetime.strptime(self.end_time, '%H:%M').time()
        else:
            end_time = self.end_time

        start = timedelta(hours=start_time.hour, minutes=start_time.minute)
        end = timedelta(hours=end_time.hour, minutes=end_time.minute)

        duration = (end - start).seconds / 3600

        if duration < 1:
            duration = 1

        # Convert Decimal to float for calculation
        total_price = duration * float(self.terrain.price_per_hour)

        return total_price
    



class Coach(models.Model):
    name = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    experience = models.IntegerField(null=True)  # Allow experience to be null

    class Meta:
        pass  # Use default table name
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
        db_table = 'coach_reservations'  # Use a different table name

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


# Equipment Model
class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('racket', 'Tennis Racket'),
        ('balls', 'Tennis Balls'),
        ('shoes', 'Tennis Shoes'),
        ('bag', 'Tennis Bag'),
        ('strings', 'Racket Strings'),
        ('grip', 'Racket Grip'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    brand = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='equipment/', blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.name}"


# Equipment Order Model
class EquipmentOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.equipment.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.equipment.name}"


# Subscription Model
class Subscription(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
        ('vip', 'VIP Plan'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    auto_renew = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan_type} ({self.status})"

    @property
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()


# Tournament Model
class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ('singles', 'Singles'),
        ('doubles', 'Doubles'),
        ('mixed', 'Mixed Doubles'),
    ]

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    max_participants = models.IntegerField()
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2)
    prize_money = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tournaments')

    def __str__(self):
        return f"{self.name} ({self.tournament_type})"


# Tournament Registration Model
class TournamentRegistration(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    partner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tournament_partnerships')
    registration_date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('tournament', 'player')

    def __str__(self):
        return f"{self.player.username} - {self.tournament.name}"


# Notification Model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reservation', 'Reservation'),
        ('tournament', 'Tournament'),
        ('equipment', 'Equipment'),
        ('subscription', 'Subscription'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# Payment Model
class Payment(models.Model):
    PAYMENT_TYPES = [
        ('reservation', 'Court Reservation'),
        ('coach', 'Coach Session'),
        ('equipment', 'Equipment Purchase'),
        ('subscription', 'Subscription'),
        ('tournament', 'Tournament Entry'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return f"Payment #{self.id} - {self.user.username} - ${self.amount}"
