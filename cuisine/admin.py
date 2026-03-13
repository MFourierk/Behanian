from django.contrib import admin
from .models import (
    Fournisseur,
    CategorieIngredient,
    UniteIngredient,
    Ingredient,
    MouvementStockCuisine,
    BonCommandeCuisine,
    LigneBonCommandeCuisine,
    BonReceptionCuisine,
    LigneBonReceptionCuisine,
    CategoriePlat,
    FicheTechnique,
    LigneFicheTechnique,
    Plat,
    InventaireCuisine,
    LigneInventaireCuisine,
    CasseCuisine,
    LigneCasseCuisine,
)

admin.site.register(Fournisseur)
admin.site.register(CategorieIngredient)
admin.site.register(UniteIngredient)
admin.site.register(Ingredient)
admin.site.register(MouvementStockCuisine)
admin.site.register(BonCommandeCuisine)
admin.site.register(LigneBonCommandeCuisine)
admin.site.register(BonReceptionCuisine)
admin.site.register(LigneBonReceptionCuisine)
admin.site.register(CategoriePlat)
admin.site.register(FicheTechnique)
admin.site.register(LigneFicheTechnique)
admin.site.register(Plat)
admin.site.register(InventaireCuisine)
admin.site.register(LigneInventaireCuisine)
admin.site.register(CasseCuisine)
admin.site.register(LigneCasseCuisine)