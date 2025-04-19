from django.conf import settings
from django.db import models

class Match(models.Model):
    MATCH_TYPE_CHOICES = [
        ('amical', 'Amical'),
        ('tournoi', 'Tournoi'),
    ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_matches')
    opponent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='joined_matches')
    match_type = models.CharField(max_length=10, choices=MATCH_TYPE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_by.email} vs {self.opponent.email if self.opponent else '???'} ({self.match_type})"
