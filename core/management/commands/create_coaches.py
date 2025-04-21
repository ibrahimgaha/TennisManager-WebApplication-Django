from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create 3 static coach users'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        coaches = [
                {'username': 'ibrahimm', 'email': 'ibrahim@example.com', 'password': '12345678x'},
                {'username': 'melekk', 'email': 'melek@example.com', 'password': 'pass1234'},
                {'username': 'fatmaa', 'email': 'fatma@example.com', 'password': 'pass1234'},
        ]

        for coach in coaches:
            if not User.objects.filter(email=coach['email']).exists():
                User.objects.create_user(
                    username=coach['username'],
                    email=coach['email'],
                    password=coach['password'],
                    role='coach'  # Make sure your User model has this field
                )
                self.stdout.write(self.style.SUCCESS(f"Created: {coach['email']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {coach['email']}"))
