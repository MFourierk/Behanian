"""
Admin Django — Dashboard / Remise à Zéro Totale
================================================
La remise TOTALE est enregistrée ici comme vue admin personnalisée,
accessible uniquement depuis /admin/reset-total/.
"""
import json
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .models import Configuration, JournalReset


# ── Configuration singleton ───────────────────────────────────────────────────

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display    = ['nom_complexe', 'telephone', 'email']
    fieldsets = [
        ('Identité du complexe', {
            'fields': ['nom_complexe', 'adresse', 'telephone', 'email', 'site_web']
        }),
        ('Documents', {
            'fields': ['notes_pied_de_page']
        }),
    ]

    def has_add_permission(self, request):
        return not Configuration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── Journal des remises à zéro ────────────────────────────────────────────────

@admin.register(JournalReset)
class JournalResetAdmin(admin.ModelAdmin):
    list_display  = ['date', 'utilisateur', 'type_reset', 'succes', 'backup_path']
    list_filter   = ['type_reset', 'succes']
    readonly_fields = [
        'date', 'utilisateur', 'type_reset', 'modules',
        'counts_avant', 'backup_path', 'succes', 'erreur'
    ]
    ordering = ['-date']

    def has_add_permission(self, request):
        return False  # Le journal est en lecture seule

    def has_delete_permission(self, request, obj=None):
        return False  # Immuable


# ── Remise Totale — vue admin personnalisée ───────────────────────────────────

def _superuser_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux superadministrateurs.")
        return view_func(request, *args, **kwargs)
    return wrapper


def total_reset_confirm(request):
    """Affiche la page de confirmation de la remise totale (admin Django)."""
    from .reset_actions import get_counts, get_counts_json, get_total, MODULES

    counts = get_counts()
    total  = get_total(counts)
    context = {
        **admin.site.each_context(request),
        'title':       '🔴 Remise à Zéro Totale',
        'counts':      counts,
        'counts_json': get_counts_json(counts),
        'total':       total,
        'modules':     MODULES,
        'opts':        {'app_label': 'dashboard'},   # breadcrumb admin
    }
    return render(request, 'admin/reset/total_confirm.html', context)


@require_POST
def total_reset_execute(request):
    """Exécute la remise totale (POST uniquement, admin Django)."""
    from .reset_actions import get_counts, reset_complet, MODULES

    # Triple sécurité
    code = request.POST.get('code_confirmation', '').strip().upper()
    if code != 'RESET TOTAL':
        messages.error(request, 'Code incorrect. Saisissez exactement : RESET TOTAL')
        return redirect('admin:total_reset_confirm')

    mdp = request.POST.get('password_admin', '').strip()
    if not request.user.check_password(mdp):
        messages.error(request, 'Mot de passe administrateur incorrect.')
        return redirect('admin:total_reset_confirm')

    confirm2 = request.POST.get('confirm_checkbox', '').strip()
    if confirm2 != 'on':
        messages.error(request, 'Vous devez cocher la case de confirmation finale.')
        return redirect('admin:total_reset_confirm')

    try:
        reset_complet(user=request.user)
        messages.success(request, '✅ Remise à zéro totale effectuée. Le système est vierge.')
    except Exception as e:
        messages.error(request, f'❌ Erreur critique lors de la remise totale : {e}')
        return redirect('admin:total_reset_confirm')

    return redirect('admin:total_reset_success')


def total_reset_success(request):
    """Page de confirmation après remise totale."""
    from .reset_actions import get_counts, get_total, MODULES
    counts = get_counts()
    context = {
        **admin.site.each_context(request),
        'title':   '✅ Remise Totale Effectuée',
        'counts':  counts,
        'total':   get_total(counts),
        'modules': MODULES,
        'opts':    {'app_label': 'dashboard'},
    }
    return render(request, 'admin/reset/total_success.html', context)


# ── Injection des URLs dans le site admin Django ──────────────────────────────

_original_get_urls = admin.site.__class__.get_urls


def _custom_get_urls(self):
    custom = [
        path(
            'reset-total/',
            self.admin_view(_superuser_only(total_reset_confirm)),
            name='total_reset_confirm',
        ),
        path(
            'reset-total/execute/',
            self.admin_view(_superuser_only(total_reset_execute)),
            name='total_reset_execute',
        ),
        path(
            'reset-total/success/',
            self.admin_view(_superuser_only(total_reset_success)),
            name='total_reset_success',
        ),
    ]
    return custom + _original_get_urls(self)


admin.site.__class__.get_urls = _custom_get_urls
admin.site.index_template = 'admin/custom_index.html'
