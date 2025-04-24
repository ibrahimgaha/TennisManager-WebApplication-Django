from rest_framework import serializers
from .models import Match

class MatchSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    opponent_email = serializers.EmailField(source='opponent.email', read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'created_by', 'created_by_email',
            'opponent', 'opponent_email',
            'match_type', 'date', 'time', 'location',
            'notes', 'is_confirmed', 'created_at'
        ]
        read_only_fields = ['created_by', 'is_confirmed', 'created_at']
