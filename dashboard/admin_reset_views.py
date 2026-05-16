"""
Vues pour la remise à zéro PARTIELLE et PERSONNALISÉE — BEHANIAN ERP
Accessible depuis /system/reset/ (superuser uniquement).

La remise TOTALE est réservée à la console Django Admin (/admin/).
"""
import json
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from .reset_actions import (
    get_counts, get_counts_json, get_total,
    reset_modules, journal_reset, backup_json,
    MODULES
)


def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux administrateurs système.")
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_member_required
@superuser_required
def reset_dashboard(request):
    counts      = get_counts()
    total       = get_total(counts)
    context = {
        'title':        'Remise à Zéro — BEHANIAN ERP',
        'counts':       counts,
        'counts_json':  get_counts_json(counts),
        'total':        total,
        'modules':      MODULES,
    }
    return render(request, 'admin/reset/dashboard.html', context)


@staff_member_required
@superuser_required
def reset_confirm(request, type_reset):
    """Page de confirmation avec sélection modulaire."""
    # La remise TOTALE est réservée à l'admin Django
    if type_reset not in ('partiel', 'personnalise'):
        messages.error(request, "La remise totale est accessible uniquement depuis la console d'administration.")
        return redirect('admin_reset_dashboard')

    counts      = get_counts()
    counts_json = get_counts_json(counts)

    if type_reset == 'partiel':
        titre       = '🟡 Remise Partielle'
        color       = '#D97706'
        description = (
            'Supprime toutes les transactions et remet les compteurs à 0. '
            'Les articles, utilisateurs, plats, boissons, stocks et toute la '
            'configuration sont conservés.'
        )
        # Pré-cocher tout sauf stocks cave/cuisine
        preselection = {
            mod: [k for k in info['sous_modules'] if k != 'stocks']
            for mod, info in MODULES.items()
        }

    else:  # personnalise
        titre       = '🟣 Remise Personnalisée'
        color       = '#7C3AED'
        description = 'Sélectionnez précisément les modules et données à supprimer.'
        preselection = {}

    context = {
        'title':             titre,
        'type_reset':        type_reset,
        'description':       description,
        'color':             color,
        'modules':           MODULES,
        'counts':            counts,
        'counts_json':       counts_json,
        'preselection_json': json.dumps(preselection),
    }
    return render(request, 'admin/reset/confirm.html', context)


@staff_member_required
@superuser_required
@require_POST
def reset_execute(request, type_reset):
    """Exécute la remise partielle ou personnalisée."""
    if type_reset not in ('partiel', 'personnalise'):
        return redirect('admin_reset_dashboard')

    # Double sécurité : code CONFIRMER
    code = request.POST.get('code_confirmation', '').strip().upper()
    if code != 'CONFIRMER':
        messages.error(request, 'Code de confirmation incorrect. Saisissez exactement : CONFIRMER')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    # Double sécurité : mot de passe admin
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

    # Backup + comptages avant
    counts_avant = get_counts()
    backup_path  = backup_json(type_reset, request.user)

    try:
        reset_modules(selection)
        journal_reset(
            type_reset   = type_reset,
            user         = request.user,
            modules_selection = selection,
            counts_avant = counts_avant,
            backup_path  = backup_path,
            succes       = True,
        )
        nb = len(selection)
        messages.success(request, f'✅ Remise à zéro effectuée sur {nb} module(s).')
    except Exception as e:
        journal_reset(
            type_reset   = type_reset,
            user         = request.user,
            modules_selection = selection,
            counts_avant = counts_avant,
            backup_path  = backup_path,
            succes       = False,
            erreur       = str(e),
        )
        messages.error(request, f'❌ Erreur : {e}')
        return redirect('admin_reset_dashboard')

    return redirect('admin_reset_success', type_reset=type_reset)


@staff_member_required
@superuser_required
def reset_success(request, type_reset):
    counts     = get_counts()
    total      = get_total(counts)
    context = {
        'title':      'Remise à Zéro Effectuée',
        'type_reset': type_reset,
        'counts':     counts,
        'counts_json': get_counts_json(counts),
        'total':      total,
        'modules':    MODULES,
    }
    return render(request, 'admin/reset/success.html', context)
