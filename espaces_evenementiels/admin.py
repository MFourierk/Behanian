from django.contrib import admin
from .models import EspaceEvenementiel, ReservationEspace

@admin.register(EspaceEvenementiel)
class EspaceEvenementielAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_espace', 'capacite', 'prix_heure', 'statut']
    list_filter = ['type_espace', 'statut']
    search_fields = ['nom']

@admin.register(ReservationEspace)
class ReservationEspaceAdmin(admin.ModelAdmin):
    list_display = ['nom_client', 'espace', 'date_debut', 'date_fin', 'prix_total', 'statut']
    list_filter = ['statut', 'date_debut']
    search_fields = ['nom_client']