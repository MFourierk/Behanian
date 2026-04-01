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

# ── Forfaits ────────────────────────────────────────────────────────────────
from .models import Forfait, LigneForfait
from django.contrib import admin as django_admin

class LigneForfaitInline(django_admin.TabularInline):
    model = LigneForfait
    extra = 1
    fields = ['type_item', 'plat', 'boisson', 'libelle', 'quantite', 'ordre']

@django_admin.register(Forfait)
class ForfaitAdmin(django_admin.ModelAdmin):
    list_display  = ['nom', 'module', 'prix', 'disponible', 'nb_items']
    list_filter   = ['module', 'disponible']
    search_fields = ['nom']
    inlines       = [LigneForfaitInline]

    def nb_items(self, obj):
        return obj.lignes.count()
    nb_items.short_description = "Nb éléments"
