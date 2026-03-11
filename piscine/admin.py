from django.contrib import admin
from .models import AccesPiscine, TarifPiscine, ConsommationPiscine

@admin.register(TarifPiscine)
class TarifPiscineAdmin(admin.ModelAdmin):
    list_display = ['type_client', 'prix_unitaire']

@admin.register(AccesPiscine)
class AccesPiscineAdmin(admin.ModelAdmin):
    list_display = ['nom_client', 'type_client', 'nombre_personnes', 'prix_total', 'date_entree', 'date_sortie']
    list_filter = ['type_client', 'date_entree']
    search_fields = ['nom_client']

@admin.register(ConsommationPiscine)
class ConsommationPiscineAdmin(admin.ModelAdmin):
    list_display = ['acces', 'produit', 'quantite', 'prix_unitaire', 'date_creation']