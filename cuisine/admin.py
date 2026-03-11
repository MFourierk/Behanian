from django.contrib import admin
from .models import (
    Ingredient, FicheTechnique, LigneFicheTechnique, MouvementStock, 
    CategorieIngredient, Fournisseur, Unite, Emplacement
)

@admin.register(CategorieIngredient)
class CategorieIngredientAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'personne_contact', 'telephone', 'email')
    search_fields = ('nom', 'personne_contact')

@admin.register(Unite)
class UniteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'abreviation')
    search_fields = ('nom', 'abreviation')

@admin.register(Emplacement)
class EmplacementAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'quantite_stock', 'unite', 'prix_moyen', 'prix_vente', 'en_alerte')
    list_filter = ('categorie', 'unite')
    search_fields = ('nom', 'categorie__nom')
    ordering = ('nom',)

class LigneFicheTechniqueInline(admin.TabularInline):
    model = LigneFicheTechnique
    extra = 1

@admin.register(FicheTechnique)
class FicheTechniqueAdmin(admin.ModelAdmin):
    list_display = ['plat', 'temps_preparation', 'nombre_portions', 'cout_revient']
    search_fields = ['plat__nom']
    inlines = [LigneFicheTechniqueInline]

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date', 'ingredient', 'type_mouvement', 'quantite', 'fournisseur', 'utilisateur')
    list_filter = ('type_mouvement', 'date', 'fournisseur', 'utilisateur')
    search_fields = ('ingredient__nom', 'commentaire', 'fournisseur__nom')
    autocomplete_fields = ['ingredient', 'utilisateur', 'fournisseur']

