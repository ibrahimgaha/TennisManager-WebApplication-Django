from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Coach

User = get_user_model()

@receiver(post_save, sender=User)
def create_coach_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Coach profile when a User with role='coach' is created
    """
    if created and instance.role == 'coach':
        # Create coach profile with default values
        Coach.objects.create(
            user=instance,
            name=f"{instance.first_name} {instance.last_name}".strip() or instance.username,
            email=instance.email,
            price_per_hour=50.00,  # Default price
            experience=1,  # Default experience
            bio=f"Professional tennis coach with expertise in player development.",
            specialization="General Tennis Coaching",
            is_active=True
        )
        print(f"✅ Created Coach profile for user: {instance.username}")

@receiver(post_save, sender=User)
def update_coach_profile(sender, instance, created, **kwargs):
    """
    Update Coach profile when User information changes
    """
    if not created and instance.role == 'coach':
        try:
            coach = Coach.objects.get(user=instance)
            # Update coach information based on user changes
            coach.name = f"{instance.first_name} {instance.last_name}".strip() or instance.username
            coach.email = instance.email
            coach.save()
            print(f"✅ Updated Coach profile for user: {instance.username}")
        except Coach.DoesNotExist:
            # If coach profile doesn't exist, create it
            Coach.objects.create(
                user=instance,
                name=f"{instance.first_name} {instance.last_name}".strip() or instance.username,
                email=instance.email,
                price_per_hour=50.00,
                experience=1,
                bio=f"Professional tennis coach with expertise in player development.",
                specialization="General Tennis Coaching",
                is_active=True
            )
            print(f"✅ Created missing Coach profile for user: {instance.username}")
