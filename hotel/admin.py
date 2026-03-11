from django.contrib import admin
from .models import Chambre, Client, Reservation

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ['numero', 'type_chambre', 'etage', 'capacite', 'prix_nuit', 'statut']
    list_filter = ['type_chambre', 'statut', 'etage']
    search_fields = ['numero']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'telephone', 'email']
    search_fields = ['nom', 'prenom', 'telephone']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'chambre', 'client', 'date_arrivee', 'date_depart', 'statut']
    list_filter = ['statut', 'date_arrivee']
    search_fields = ['client__nom', 'chambre__numero']