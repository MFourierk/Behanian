from django.contrib import admin
from .models import CaisseSession, MouvementCaisse, PrelevementBanque

@admin.register(CaisseSession)
class CaisseSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'opened_at', 'closed_at', 'is_open']
    list_filter = ['is_open', 'opened_at']
    search_fields = ['user__username']

@admin.register(MouvementCaisse)
class MouvementCaisseAdmin(admin.ModelAdmin):
    list_display = ['date', 'type', 'module', 'montant', 'mode_paiement', 'cree_par', 'valide']
    list_filter = ['type', 'module', 'mode_paiement', 'valide']
    search_fields = ['description', 'reference']
    date_hierarchy = 'date'

@admin.register(PrelevementBanque)
class PrelevementBanqueAdmin(admin.ModelAdmin):
    list_display = ['date', 'montant', 'banque', 'reference', 'cree_par', 'valide']
    list_filter = ['valide', 'banque']
    search_fields = ['banque', 'reference']
    date_hierarchy = 'date'

