from django.contrib import admin
from .models import Configuration

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('nom_complexe', 'telephone', 'email')

    # Empêcher l'ajout de nouvelles configurations via l'admin
    def has_add_permission(self, request):
        return False

    # Empêcher la suppression des configurations via l'admin
    def has_delete_permission(self, request, obj=None):
        return False
