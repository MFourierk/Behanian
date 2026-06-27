from django.contrib import admin
from .models import (
    BoissonBar, CategorieBar, MouvementStockBar,
    BonCommandeBar, LigneBonCommandeBar,
    BonReceptionBar, LigneBonReceptionBar,
    InventaireBar, LigneInventaireBar,
    CasseBar, LigneCasseBar,
)

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

@admin.register(LigneBonCommandeBar)
class LigneBonCommandeBarAdmin(admin.ModelAdmin):
    list_display = ('bon', 'article', 'quantite_commandee', 'prix_unitaire')
    list_filter = ('bon__statut',)
    search_fields = ('article__nom', 'bon__numero')

@admin.register(BonReceptionBar)
class BonReceptionBarAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fournisseur', 'date_reception', 'statut')
    list_filter = ('statut', 'fournisseur')
    search_fields = ('numero',)
    date_hierarchy = 'date_reception'

@admin.register(LigneBonReceptionBar)
class LigneBonReceptionBarAdmin(admin.ModelAdmin):
    list_display = ('bon', 'article', 'quantite_recue', 'prix_unitaire')
    search_fields = ('article__nom', 'bon__numero')

@admin.register(InventaireBar)
class InventaireBarAdmin(admin.ModelAdmin):
    list_display = ('numero', 'statut', 'cree_par', 'date_creation')
    list_filter = ('statut',)
    date_hierarchy = 'date_creation'

@admin.register(LigneInventaireBar)
class LigneInventaireBarAdmin(admin.ModelAdmin):
    list_display = ('inventaire', 'article', 'quantite_theorique', 'quantite_comptee')
    search_fields = ('article__nom',)

@admin.register(CasseBar)
class CasseBarAdmin(admin.ModelAdmin):
    list_display = ('numero', 'type_casse', 'statut', 'declare_par', 'date_casse')
    list_filter = ('type_casse', 'statut')
    date_hierarchy = 'date_casse'

@admin.register(LigneCasseBar)
class LigneCasseBarAdmin(admin.ModelAdmin):
    list_display = ('casse', 'article', 'quantite', 'prix_unitaire')
    search_fields = ('article__nom',)
