from django.contrib import admin
from .models import Facture, Proforma, Avoir, Client, Service, Article, LigneFacture, LigneProforma, LigneAvoir, Ticket

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'telephone', 'email', 'nif', 'stat']
    search_fields = ['nom', 'telephone', 'email']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'service', 'prix_unitaire', 'actif']
    list_filter = ['service', 'actif']
    search_fields = ['nom']

class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 0

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date_facturation', 'total', 'statut']
    list_filter = ['statut', 'date_facturation']
    search_fields = ['numero', 'client__nom']
    inlines = [LigneFactureInline]

class LigneProformaInline(admin.TabularInline):
    model = LigneProforma
    extra = 0

@admin.register(Proforma)
class ProformaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date_creation', 'date_validite', 'total', 'statut']
    list_filter = ['statut', 'date_creation']
    search_fields = ['numero', 'client__nom']
    inlines = [LigneProformaInline]

class LigneAvoirInline(admin.TabularInline):
    model = LigneAvoir
    extra = 0

@admin.register(Avoir)
class AvoirAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date_avoir', 'total', 'statut']
    list_filter = ['statut', 'date_avoir']
    search_fields = ['numero', 'client__nom']
    inlines = [LigneAvoirInline]

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['numero', 'date_creation', 'montant_total', 'module', 'est_duplicata']
    list_filter = ['module', 'date_creation']
    search_fields = ['numero', 'contenu']

