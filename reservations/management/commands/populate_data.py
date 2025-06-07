from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reservations.models import (
    Terrain, Coach, Equipment, Tournament, Notification
)
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create terrains
        terrains_data = [
            {'name': 'Court Central', 'location': 'Main Building', 'price_per_hour': 50.00},
            {'name': 'Court A', 'location': 'East Wing', 'price_per_hour': 40.00},
            {'name': 'Court B', 'location': 'East Wing', 'price_per_hour': 40.00},
            {'name': 'Court C', 'location': 'West Wing', 'price_per_hour': 35.00},
            {'name': 'Practice Court', 'location': 'Training Area', 'price_per_hour': 25.00},
        ]
        
        for terrain_data in terrains_data:
            terrain, created = Terrain.objects.get_or_create(
                name=terrain_data['name'],
                defaults=terrain_data
            )
            if created:
                self.stdout.write(f'Created terrain: {terrain.name}')
        
        # Create coaches
        coaches_data = [
            {'name': 'John Smith', 'email': 'john.smith@tennis.com', 'price_per_hour': 80.00, 'phone': '+1234567890', 'experience': 10},
            {'name': 'Maria Garcia', 'email': 'maria.garcia@tennis.com', 'price_per_hour': 75.00, 'phone': '+1234567891', 'experience': 8},
            {'name': 'David Wilson', 'email': 'david.wilson@tennis.com', 'price_per_hour': 70.00, 'phone': '+1234567892', 'experience': 6},
            {'name': 'Sarah Johnson', 'email': 'sarah.johnson@tennis.com', 'price_per_hour': 85.00, 'phone': '+1234567893', 'experience': 12},
        ]
        
        for coach_data in coaches_data:
            coach, created = Coach.objects.get_or_create(
                email=coach_data['email'],
                defaults=coach_data
            )
            if created:
                self.stdout.write(f'Created coach: {coach.name}')
        
        # Create equipment
        equipment_data = [
            {'name': 'Pro Racket', 'type': 'racket', 'brand': 'Wilson', 'price': 150.00, 'stock_quantity': 20, 'description': 'Professional tennis racket'},
            {'name': 'Championship Balls', 'type': 'balls', 'brand': 'Penn', 'price': 8.00, 'stock_quantity': 100, 'description': 'Official tournament balls'},
            {'name': 'Court Shoes', 'type': 'shoes', 'brand': 'Nike', 'price': 120.00, 'stock_quantity': 15, 'description': 'Professional tennis shoes'},
            {'name': 'Tennis Bag', 'type': 'bag', 'brand': 'Head', 'price': 80.00, 'stock_quantity': 25, 'description': 'Large tennis equipment bag'},
            {'name': 'Racket Strings', 'type': 'strings', 'brand': 'Babolat', 'price': 25.00, 'stock_quantity': 50, 'description': 'High-quality racket strings'},
            {'name': 'Grip Tape', 'type': 'grip', 'brand': 'Tourna', 'price': 5.00, 'stock_quantity': 75, 'description': 'Non-slip grip tape'},
        ]
        
        for equip_data in equipment_data:
            equipment, created = Equipment.objects.get_or_create(
                name=equip_data['name'],
                brand=equip_data['brand'],
                defaults=equip_data
            )
            if created:
                self.stdout.write(f'Created equipment: {equipment.name}')
        
        # Create tournaments
        tournaments_data = [
            {
                'name': 'Spring Championship',
                'description': 'Annual spring tennis championship for all skill levels',
                'tournament_type': 'singles',
                'start_date': datetime.now() + timedelta(days=30),
                'end_date': datetime.now() + timedelta(days=32),
                'registration_deadline': datetime.now() + timedelta(days=20),
                'max_participants': 32,
                'entry_fee': 50.00,
                'prize_money': 1000.00,
            },
            {
                'name': 'Doubles Tournament',
                'description': 'Exciting doubles tournament with great prizes',
                'tournament_type': 'doubles',
                'start_date': datetime.now() + timedelta(days=45),
                'end_date': datetime.now() + timedelta(days=47),
                'registration_deadline': datetime.now() + timedelta(days=35),
                'max_participants': 16,
                'entry_fee': 75.00,
                'prize_money': 1500.00,
            }
        ]
        
        # Get or create admin user for tournaments
        try:
            admin_user = User.objects.get(email='admin@tennis.com')
        except User.DoesNotExist:
            admin_user = User.objects.create(
                username='admin_tennis',
                email='admin@tennis.com',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')

        
        for tournament_data in tournaments_data:
            tournament_data['created_by'] = admin_user
            tournament, created = Tournament.objects.get_or_create(
                name=tournament_data['name'],
                defaults=tournament_data
            )
            if created:
                self.stdout.write(f'Created tournament: {tournament.name}')
        
        # Create sample users
        sample_users = [
            {'username': 'player1_tennis', 'email': 'player1@tennis.com', 'role': 'joueur'},
            {'username': 'player2_tennis', 'email': 'player2@tennis.com', 'role': 'joueur'},
            {'username': 'coach1_tennis', 'email': 'coach1@tennis.com', 'role': 'coach'},
            {'username': 'subscriber1_tennis', 'email': 'subscriber1@tennis.com', 'role': 'abonnée'},
        ]

        for user_data in sample_users:
            try:
                user = User.objects.get(email=user_data['email'])
                self.stdout.write(f'User already exists: {user.username}')
            except User.DoesNotExist:
                user = User.objects.create(**user_data)
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample data!'))
