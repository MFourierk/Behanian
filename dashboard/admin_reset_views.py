import json
"""
Vues admin pour la remise à zéro modulaire — BEHANIAN
Accessible depuis /system/reset/  (superuser uniquement)
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from .reset_actions import get_counts, get_total, reset_modules, reset_partiel, reset_complet, MODULES


def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux administrateurs système.")
        return view_func(request, *args, **kwargs)
    return wrapper


def _make_flat(counts):
    """Aplatir les counts pour le template."""
    flat = {}
    for module, data in counts.items():
        if isinstance(data, dict):
            for key, val in data.items():
                flat[f"{module}__{key}"] = val
    return flat


@staff_member_required
@superuser_required
def reset_dashboard(request):
    counts = get_counts()
    total  = get_total(counts)
    context = {
        'title':   'Remise à Zéro — BEHANIAN',
        'counts':  counts,
        'flat':    _make_flat(counts),
        'total':   total,
        'modules': MODULES,
    }
    return render(request, 'admin/reset/dashboard.html', context)


@staff_member_required
@superuser_required
def reset_confirm(request, type_reset):
    """Page de confirmation avec checkboxes modulaires."""
    if type_reset not in ('partiel', 'complet', 'personnalise'):
        return redirect('admin_reset_dashboard')

    counts = get_counts()
    flat   = _make_flat(counts)

    if type_reset == 'partiel':
        titre       = 'Remise à Zéro Partielle'
        color       = '#D97706'
        description = 'Supprime toutes les transactions. Les stocks sont conservés.'
        # Pré-cocher tout sauf stocks cave/cuisine
        preselection = {
            mod: list(info['sous_modules'].keys())
            for mod, info in MODULES.items()
        }
        # Décocher les stocks par défaut en partiel
        for mod in ['cave', 'cuisine']:
            preselection[mod] = [k for k in MODULES[mod]['sous_modules'] if k != 'stocks']

    elif type_reset == 'complet':
        titre       = 'Remise à Zéro Complète'
        color       = '#DC2626'
        description = 'Supprime tout y compris les stocks. Ne conserve que la structure.'
        preselection = {mod: list(info['sous_modules'].keys()) for mod, info in MODULES.items()}

    else:  # personnalise
        titre       = 'Remise à Zéro Personnalisée'
        color       = '#7C3AED'
        description = 'Sélectionnez précisément les données à supprimer.'
        preselection = {}

    context = {
        'title':            titre,
        'type_reset':       type_reset,
        'description':      description,
        'color':            color,
        'modules':          MODULES,
        'counts':           counts,
        'flat':             flat,
        'preselection':     preselection,
        'preselection_json':json.dumps(preselection),
    }
    return render(request, 'admin/reset/confirm.html', context)


@staff_member_required
@superuser_required
@require_POST
def reset_execute(request, type_reset):
    """Exécute le reset selon la sélection des checkboxes."""

    # Double sécurité
    code = request.POST.get('code_confirmation', '').strip().upper()
    if code != 'CONFIRMER':
        messages.error(request, 'Code de confirmation incorrect. Saisissez exactement : CONFIRMER')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    mdp = request.POST.get('password_admin', '').strip()
    if not request.user.check_password(mdp):
        messages.error(request, 'Mot de passe administrateur incorrect.')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    # Construire la sélection depuis les checkboxes POST
    selection = {}
    for mod in MODULES:
        sous_coches = request.POST.getlist(f'sous_{mod}')
        if sous_coches:
            selection[mod] = sous_coches

    if not selection:
        messages.error(request, 'Aucun module sélectionné. Cochez au moins un élément.')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    try:
        reset_modules(selection)
        nb_modules = len(selection)
        messages.success(request, f'✅ Remise à zéro effectuée sur {nb_modules} module(s).')
    except Exception as e:
        messages.error(request, f'❌ Erreur : {e}')
        return redirect('admin_reset_dashboard')

    return redirect('admin_reset_success', type_reset=type_reset)


@staff_member_required
@superuser_required
def reset_success(request, type_reset):
    counts = get_counts()
    total  = get_total(counts)
    context = {
        'title':      'Remise à Zéro Effectuée',
        'type_reset': type_reset,
        'counts':     counts,
        'flat':       _make_flat(counts),
        'total':      total,
        'modules':    MODULES,
    }
    return render(request, 'admin/reset/success.html', context)
