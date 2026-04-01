from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect


class ResetAdminSite(admin.AdminSite):
    """Admin site personnalisé avec lien vers la remise à zéro."""
    pass


# Ajouter le lien dans le menu admin via app_index
def get_reset_url(request):
    return redirect('/admin/reset/')


admin.site.index_template = 'admin/custom_index.html'
