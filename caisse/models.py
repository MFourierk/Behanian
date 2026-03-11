from django.db import models
from django.contrib.auth.models import User

class CaisseSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='caisse_sessions')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return f"Session de caisse de {self.user.username} - Ouverte à {self.opened_at}"
