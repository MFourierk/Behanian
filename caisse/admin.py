from django.contrib import admin
from .models import CaisseSession

@admin.register(CaisseSession)
class CaisseSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'opened_at', 'closed_at', 'is_open']
    list_filter = ['is_open', 'opened_at']
    search_fields = ['user__username']

