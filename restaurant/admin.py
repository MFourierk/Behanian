from django.contrib import admin
from .models import Table, CategorieMenu, PlatMenu, Commande, LigneCommande

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['numero', 'capacite', 'statut']
    list_filter = ['statut']

@admin.register(CategorieMenu)
class CategorieMenuAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ordre']
    ordering = ['ordre']

@admin.register(PlatMenu)
class PlatMenuAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie', 'prix', 'temps_preparation', 'disponible']
    list_filter = ['categorie', 'disponible']
    search_fields = ['nom']

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'nom_client', 'statut', 'total', 'date_creation']
    list_filter = ['statut', 'date_creation']

@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ['commande', 'plat', 'quantite', 'prix_unitaire']