from django.contrib import admin
from .models import BoissonBar, CategorieBar, MouvementStockBar, BonCommandeBar

@admin.register(CategorieBar)
class CategorieBarAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre')
    ordering = ('ordre',)

@admin.register(BoissonBar)
class BoissonBarAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix', 'quantite_stock', 'disponible')
    list_filter = ('categorie', 'disponible')
    search_fields = ('nom', 'categorie__nom')
    ordering = ('categorie', 'nom')

@admin.register(MouvementStockBar)
class MouvementStockBarAdmin(admin.ModelAdmin):
    list_display = ('date', 'boisson', 'type_mouvement', 'quantite', 'utilisateur')
    list_filter = ('type_mouvement', 'date', 'utilisateur')
    search_fields = ('boisson__nom', 'commentaire')

@admin.register(BonCommandeBar)
class BonCommandeBarAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fournisseur', 'date_commande', 'statut', 'total')
    list_filter = ('statut', 'fournisseur')
    search_fields = ('numero',)
    date_hierarchy = 'date_commande'
