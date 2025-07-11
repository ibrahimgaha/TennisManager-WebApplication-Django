from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'avatar','role']

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            avatar=validated_data.get('avatar'),
            role=validated_data.get('role', 'joueur')  # Use provided role or default to 'joueur'

        )
        user.set_password(validated_data['password'])
        user.save()
        return user
