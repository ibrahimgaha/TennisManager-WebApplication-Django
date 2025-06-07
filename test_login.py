#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis_manager.settings')
django.setup()

from core.models import User

# Test user roles
print("Testing user roles in database:")
users = User.objects.all()
for user in users:
    print(f"Username: {user.username}, Email: {user.email}, Role: {user.role}")

print("\nTesting custom login view...")
from core.views import CustomTokenObtainPairView
print("Custom login view imported successfully!")

# Test the serializer
from core.views import CustomTokenObtainPairSerializer
print("Custom serializer imported successfully!")

print("\nAll imports successful! The login fix should work.")
