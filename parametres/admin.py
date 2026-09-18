from django.contrib import admin
from .models import Coordonnees, Employe

@admin.register(Coordonnees)
class CoordonneesAdmin(admin.ModelAdmin):
    list_display = ('nom_complexe', 'telephone1', 'email')

    def has_add_permission(self, request):
        # Allow adding if no instance exists yet
        return not Coordonnees.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # For simplicity, let's not allow deletion from the admin
        return False


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ('nom_complet', 'poste', 'salaire_base', 'actif')
    list_filter   = ('actif',)
    search_fields = ('nom_complet', 'poste')
    list_editable = ('salaire_base', 'actif')
