"""
Vues admin pour la remise à zéro — BEHANIAN
Accessibles depuis /admin/reset/
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden
from .reset_actions import get_counts, reset_partiel, reset_complet


def superuser_required(view_func):
    """Décorateur : réserve la vue aux superutilisateurs uniquement."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden("Accès réservé aux administrateurs système.")
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_member_required
@superuser_required
def reset_dashboard(request):
    """Page principale du menu Remise à Zéro."""
    counts = get_counts()
    total = sum(
        v if isinstance(v, int) else 0
        for module in counts.values()
        for v in (module.values() if isinstance(module, dict) else [])
    )

    # Aplatir les counts pour le template (pas d'espaces dans les clés Django)
    flat = {
        'tickets':     counts.get('facturation',{}).get('Tickets', 0),
        'factures':    counts.get('facturation',{}).get('Factures', 0),
        'proformas':   counts.get('facturation',{}).get('Proformas', 0),
        'avoirs':      counts.get('facturation',{}).get('Avoirs', 0),
        'clients_fact':counts.get('facturation',{}).get('Clients facturation', 0),
        'sessions':    counts.get('caisse',{}).get('Sessions caisse', 0),
        'mouvements':  counts.get('caisse',{}).get('Mouvements caisse', 0),
        'prelevements':counts.get('caisse',{}).get('Prélèvements banque', 0),
        'resa_hotel':  counts.get('hotel',{}).get('Réservations hôtel', 0),
        'conso_hotel': counts.get('hotel',{}).get('Consommations hôtel', 0),
        'clients_hotel':counts.get('hotel',{}).get('Clients hôtel', 0),
        'commandes':   counts.get('restaurant',{}).get('Commandes restaurant', 0),
        'lignes_cmd':  counts.get('restaurant',{}).get('Lignes commande', 0),
        'mvt_cave':    counts.get('cave',{}).get('Mouvements stock cave', 0),
        'bc_cave':     counts.get('cave',{}).get('Bons commande cave', 0),
        'br_cave':     counts.get('cave',{}).get('Bons réception cave', 0),
        'inv_cave':    counts.get('cave',{}).get('Inventaires cave', 0),
        'mvt_cuisine': counts.get('cuisine',{}).get('Mouvements stock cuisine', 0),
        'br_cuisine':  counts.get('cuisine',{}).get('Bons réception cuisine', 0),
        'acces_piscine':counts.get('piscine',{}).get('Accès piscine', 0),
        'conso_piscine':counts.get('piscine',{}).get('Consommations piscine', 0),
        'resa_espaces':counts.get('espaces',{}).get('Réservations espaces', 0),
    }
    context = {
        'title': 'Remise à Zéro — BEHANIAN',
        'counts': counts,
        'flat': flat,
        'total': total,
        'modules_info': [
            {
                'key': 'facturation',
                'nom': 'Facturation',
                'icon': '📄',
                'color': '#1D4ED8',
                'light': '#EFF6FF',
                'description': 'Tickets · Factures · Proformas · Avoirs · Clients',
            },
            {
                'key': 'caisse',
                'nom': 'Caisse',
                'icon': '💰',
                'color': '#16A34A',
                'light': '#DCFCE7',
                'description': 'Sessions · Mouvements · Prélèvements banque',
            },
            {
                'key': 'hotel',
                'nom': 'Hôtel',
                'icon': '🏨',
                'color': '#2563EB',
                'light': '#DBEAFE',
                'description': 'Réservations · Consommations · Clients hôtel',
            },
            {
                'key': 'restaurant',
                'nom': 'Restaurant',
                'icon': '🍽️',
                'color': '#D35400',
                'light': '#FFF7ED',
                'description': 'Commandes · Lignes de commande',
            },
            {
                'key': 'cave',
                'nom': 'Cave / Bar',
                'icon': '🍷',
                'color': '#7C3AED',
                'light': '#F5F3FF',
                'description': 'Mouvements stock · Bons · Inventaires · Casses',
            },
            {
                'key': 'cuisine',
                'nom': 'Cuisine',
                'icon': '👨‍🍳',
                'color': '#C0392B',
                'light': '#FEF2F2',
                'description': 'Mouvements stock · Bons · Inventaires · Casses',
            },
            {
                'key': 'piscine',
                'nom': 'Piscine',
                'icon': '🏊',
                'color': '#0891B2',
                'light': '#ECFEFF',
                'description': 'Accès · Consommations',
            },
            {
                'key': 'espaces',
                'nom': 'Espaces',
                'icon': '📅',
                'color': '#16A085',
                'light': '#F0FDF4',
                'description': 'Réservations d\'espaces',
            },
        ],
    }
    return render(request, 'admin/reset/dashboard.html', context)


@staff_member_required
@superuser_required
def reset_confirm(request, type_reset):
    """Page de confirmation avec double saisie."""
    if type_reset not in ('partiel', 'complet'):
        return redirect('admin_reset_dashboard')

    if type_reset == 'partiel':
        titre = 'Remise à Zéro Partielle'
        description = 'Supprime toutes les transactions. Les stocks, articles, plats, boissons et chambres sont conservés.'
        color = '#D97706'
        warning = 'Cette action est IRRÉVERSIBLE. Toutes les transactions de test seront supprimées définitivement.'
        items = [
            'Tickets, Factures, Proformas, Avoirs',
            'Sessions et mouvements de caisse',
            'Réservations et consommations hôtel',
            'Commandes restaurant',
            'Mouvements stock, bons et inventaires Cave',
            'Mouvements stock, bons et inventaires Cuisine',
            'Accès et consommations Piscine',
            'Réservations Espaces',
            'Numérotations réinitialisées (TC-, FAC-, PRO-, AVO-...)',
        ]
        conserve = [
            'Chambres, tables, espaces, tarifs piscine',
            'Plats, catégories, boissons (stocks conservés)',
            'Ingrédients (stocks conservés)',
            'Utilisateurs, groupes, permissions',
            'Fournisseurs, catégories, unités',
        ]
    else:
        titre = 'Remise à Zéro Complète'
        description = 'Supprime TOUT sauf les utilisateurs et groupes. Repart de zéro avec une application vierge.'
        color = '#DC2626'
        warning = 'DANGER MAXIMUM — Cette action supprime toutes les données : articles, chambres, espaces, plats, boissons, stocks. Seuls les utilisateurs sont conservés. IRRÉVERSIBLE.'
        items = [
            'Tout ce que fait la remise partielle +',
            'Stocks Cave remis à 0',
            'Stocks Cuisine (ingrédients) remis à 0',
            'Clients hôtel supprimés',
        ]
        conserve = [
            'Chambres, tables, espaces (structure uniquement)',
            'Plats, catégories, boissons (quantité = 0)',
            'Ingrédients (quantité = 0)',
            'Tarifs piscine',
            'Utilisateurs, groupes, permissions',
            'Fournisseurs, catégories, unités',
        ]

    context = {
        'title': titre,
        'type_reset': type_reset,
        'description': description,
        'color': color,
        'warning': warning,
        'items': items,
        'conserve': conserve,
        'mot_de_passe_requis': 'CONFIRMER',
    }
    return render(request, 'admin/reset/confirm.html', context)


@staff_member_required
@superuser_required
@require_POST
def reset_execute(request, type_reset):
    """Exécute la remise à zéro après vérification du code de confirmation."""
    if type_reset not in ('partiel', 'complet'):
        return redirect('admin_reset_dashboard')

    # Double sécurité : vérifier le code saisi
    code_saisi = request.POST.get('code_confirmation', '').strip().upper()
    if code_saisi != 'CONFIRMER':
        messages.error(request, f'Code de confirmation incorrect. Saisissez exactement : CONFIRMER')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    # Vérifier aussi le mot de passe admin
    password_saisi = request.POST.get('password_admin', '').strip()
    if not request.user.check_password(password_saisi):
        messages.error(request, 'Mot de passe administrateur incorrect.')
        return redirect('admin_reset_confirm', type_reset=type_reset)

    try:
        if type_reset == 'partiel':
            reset_partiel()
            messages.success(request, '✅ Remise à zéro partielle effectuée avec succès. Toutes les transactions ont été supprimées.')
        else:
            reset_complet()
            messages.success(request, '✅ Remise à zéro complète effectuée. Toutes les transactions et stocks ont été remis à zéro.')
    except Exception as e:
        messages.error(request, f'❌ Erreur lors de la remise à zéro : {e}')
        return redirect('admin_reset_dashboard')

    return redirect('admin_reset_success', type_reset=type_reset)


@staff_member_required
@superuser_required
def reset_success(request, type_reset):
    """Page de succès après remise à zéro."""
    counts = get_counts()
    flat = {
        'tickets':      counts.get('facturation',{}).get('Tickets', 0),
        'factures':     counts.get('facturation',{}).get('Factures', 0),
        'sessions':     counts.get('caisse',{}).get('Sessions caisse', 0),
        'resa_hotel':   counts.get('hotel',{}).get('Réservations hôtel', 0),
        'commandes':    counts.get('restaurant',{}).get('Commandes restaurant', 0),
        'mvt_cave':     counts.get('cave',{}).get('Mouvements stock cave', 0),
        'acces_piscine':counts.get('piscine',{}).get('Accès piscine', 0),
        'resa_espaces': counts.get('espaces',{}).get('Réservations espaces', 0),
    }
    context = {
        'title': 'Remise à Zéro Effectuée',
        'type_reset': type_reset,
        'counts': counts,
        'flat': flat,
    }
    return render(request, 'admin/reset/success.html', context)
