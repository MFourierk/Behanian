from django.contrib import admin
from .models import TableBoite, Evenement, EntreeBoite, ConsommationBoite

@admin.register(TableBoite)
class TableBoiteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'type_table', 'capacite', 'prix_reservation', 'statut']
    list_filter = ['type_table', 'statut']

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'date_evenement', 'heure_debut', 'prix_entree', 'capacite_max']
    list_filter = ['date_evenement']
    search_fields = ['titre']

@admin.register(EntreeBoite)
class EntreeBoiteAdmin(admin.ModelAdmin):
    list_display = ['nom_client', 'nombre_personnes', 'prix_entree', 'evenement', 'date_entree']
    list_filter = ['date_entree', 'evenement']
    search_fields = ['nom_client']

@admin.register(ConsommationBoite)
class ConsommationBoiteAdmin(admin.ModelAdmin):
    list_display = ['table', 'nom_client', 'produit', 'quantite', 'total', 'date_creation']
    list_filter = ['date_creation']