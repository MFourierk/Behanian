from django.contrib import admin
from .models import Coordonnees, SalaireConfig

@admin.register(Coordonnees)
class CoordonneesAdmin(admin.ModelAdmin):
    list_display = ('nom_complexe', 'telephone1', 'email')

    def has_add_permission(self, request):
        # Allow adding if no instance exists yet
        return not Coordonnees.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # For simplicity, let's not allow deletion from the admin
        return False


@admin.register(SalaireConfig)
class SalaireConfigAdmin(admin.ModelAdmin):
    list_display  = ('user', 'salaire_base', 'actif_paie')
    list_filter   = ('actif_paie',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    list_editable = ('salaire_base', 'actif_paie')
    autocomplete_fields = ('user',)
