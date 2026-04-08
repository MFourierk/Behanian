"""
Logique de remise à zéro modulaire — BEHANIAN
Chaque module peut être sélectionné indépendamment.
"""
from django.db import transaction


# ── Définition des modules ─────────────────────────────────────────────────────
MODULES = {
    'facturation': {
        'label': 'Facturation',
        'color': '#1D4ED8',
        'light': '#EFF6FF',
        'icon': '📄',
        'description': 'Tickets, Factures, Proformas, Avoirs, Clients facturation',
        'sous_modules': {
            'tickets':   'Tickets (TC-)',
            'factures':  'Factures + Lignes (FAC-)',
            'proformas': 'Proformas + Lignes (PRO-)',
            'avoirs':    'Avoirs + Lignes (AVO-)',
            'clients':   'Clients facturation',
        },
    },
    'caisse': {
        'label': 'Caisse',
        'color': '#16A34A',
        'light': '#DCFCE7',
        'icon': '💰',
        'description': 'Sessions, Mouvements, Prélèvements banque',
        'sous_modules': {
            'sessions':    'Sessions de caisse',
            'mouvements':  'Mouvements de caisse',
            'prelevements':'Prélèvements banque',
        },
    },
    'hotel': {
        'label': 'Hôtel',
        'color': '#2563EB',
        'light': '#DBEAFE',
        'icon': '🏨',
        'description': 'Réservations, Consommations, Clients hôtel',
        'sous_modules': {
            'reservations':  'Réservations hôtel',
            'consommations': 'Consommations hôtel',
            'clients':       'Clients hôtel',
        },
    },
    'restaurant': {
        'label': 'Restaurant',
        'color': '#D35400',
        'light': '#FFF7ED',
        'icon': '🍽️',
        'description': 'Commandes et lignes de commande',
        'sous_modules': {
            'commandes': 'Commandes + Lignes',
        },
    },
    'cave': {
        'label': 'Cave / Bar',
        'color': '#7C3AED',
        'light': '#F5F3FF',
        'icon': '🍷',
        'description': 'Mouvements stock, Bons commande/réception, Inventaires, Casses',
        'sous_modules': {
            'mouvements':  'Mouvements de stock',
            'commandes':   'Bons de commande',
            'receptions':  'Bons de réception',
            'inventaires': 'Inventaires',
            'casses':      'Casses / Pertes',
            'stocks':      'Remettre les stocks à 0',
        },
    },
    'cuisine': {
        'label': 'Cuisine',
        'color': '#C0392B',
        'light': '#FEF2F2',
        'icon': '👨‍🍳',
        'description': 'Mouvements stock, Bons commande/réception, Inventaires, Casses',
        'sous_modules': {
            'mouvements':  'Mouvements de stock',
            'commandes':   'Bons de commande',
            'receptions':  'Bons de réception',
            'inventaires': 'Inventaires',
            'casses':      'Casses / Pertes',
            'stocks':      'Remettre les stocks à 0',
        },
    },
    'piscine': {
        'label': 'Piscine',
        'color': '#0891B2',
        'light': '#ECFEFF',
        'icon': '🏊',
        'description': 'Accès et consommations piscine',
        'sous_modules': {
            'acces':       'Accès / Tickets entrée',
            'consommations':'Consommations piscine',
        },
    },
    'espaces': {
        'label': 'Espaces Événementiels',
        'color': '#16A085',
        'light': '#F0FDF4',
        'icon': '📅',
        'description': 'Réservations d\'espaces',
        'sous_modules': {
            'reservations': 'Réservations espaces',
        },
    },
}


def get_counts():
    """Inventaire détaillé de toutes les transactions."""
    counts = {}

    try:
        from facturation.models import Ticket, Facture, Proforma, Avoir, Client
        counts['facturation'] = {
            'tickets':   Ticket.objects.count(),
            'factures':  Facture.objects.count(),
            'proformas': Proforma.objects.count(),
            'avoirs':    Avoir.objects.count(),
            'clients':   Client.objects.count(),
        }
    except Exception as e:
        counts['facturation'] = {'erreur': str(e)}

    try:
        from caisse.models import CaisseSession, MouvementCaisse, PrelevementBanque
        counts['caisse'] = {
            'sessions':    CaisseSession.objects.count(),
            'mouvements':  MouvementCaisse.objects.count(),
            'prelevements':PrelevementBanque.objects.count(),
        }
    except Exception as e:
        counts['caisse'] = {'erreur': str(e)}

    try:
        from hotel.models import Reservation, Consommation, Client as HC
        counts['hotel'] = {
            'reservations':  Reservation.objects.count(),
            'consommations': Consommation.objects.count(),
            'clients':       HC.objects.count(),
        }
    except Exception as e:
        counts['hotel'] = {'erreur': str(e)}

    try:
        from restaurant.models import Commande, LigneCommande
        counts['restaurant'] = {
            'commandes': Commande.objects.count(),
            'lignes':    LigneCommande.objects.count(),
        }
    except Exception as e:
        counts['restaurant'] = {'erreur': str(e)}

    try:
        from bar.models import MouvementStockBar, BonCommandeBar, BonReceptionBar, InventaireBar, CasseBar, BoissonBar
        counts['cave'] = {
            'mouvements':  MouvementStockBar.objects.count(),
            'commandes':   BonCommandeBar.objects.count(),
            'receptions':  BonReceptionBar.objects.count(),
            'inventaires': InventaireBar.objects.count(),
            'casses':      CasseBar.objects.count(),
            'stocks':      BoissonBar.objects.filter(quantite_stock__gt=0).count(),
        }
    except Exception as e:
        counts['cave'] = {'erreur': str(e)}

    try:
        from cuisine.models import MouvementStockCuisine, BonCommandeCuisine, BonReceptionCuisine, InventaireCuisine, CasseCuisine, Ingredient
        counts['cuisine'] = {
            'mouvements':  MouvementStockCuisine.objects.count(),
            'commandes':   BonCommandeCuisine.objects.count(),
            'receptions':  BonReceptionCuisine.objects.count(),
            'inventaires': InventaireCuisine.objects.count(),
            'casses':      CasseCuisine.objects.count(),
            'stocks':      Ingredient.objects.filter(quantite_stock__gt=0).count(),
        }
    except Exception as e:
        counts['cuisine'] = {'erreur': str(e)}

    try:
        from piscine.models import AccesPiscine, ConsommationPiscine
        counts['piscine'] = {
            'acces':        AccesPiscine.objects.count(),
            'consommations':ConsommationPiscine.objects.count(),
        }
    except Exception as e:
        counts['piscine'] = {'erreur': str(e)}

    try:
        from espaces_evenementiels.models import ReservationEspace
        counts['espaces'] = {
            'reservations': ReservationEspace.objects.count(),
        }
    except Exception as e:
        counts['espaces'] = {'erreur': str(e)}

    return counts


def get_total(counts):
    return sum(
        v for mod in counts.values()
        for k, v in (mod.items() if isinstance(mod, dict) else {}.items())
        if isinstance(v, int) and k != 'stocks'
    )


# ── Suppressions unitaires ─────────────────────────────────────────────────────

def _reset_facturation(sous=None):
    """sous = liste de clés à supprimer, ou None = tout"""
    from facturation.models import LigneAvoir, Avoir, LigneFacture, Facture, LigneProforma, Proforma, Ticket, Client
    tout = sous is None
    if tout or 'avoirs'    in sous: LigneAvoir.objects.all().delete();   Avoir.objects.all().delete()
    if tout or 'factures'  in sous: LigneFacture.objects.all().delete();  Facture.objects.all().delete()
    if tout or 'proformas' in sous: LigneProforma.objects.all().delete(); Proforma.objects.all().delete()
    if tout or 'tickets'   in sous: Ticket.objects.all().delete()
    if tout or 'clients'   in sous: Client.objects.all().delete()


def _reset_caisse(sous=None):
    from caisse.models import MouvementCaisse, PrelevementBanque, CaisseSession
    tout = sous is None
    if tout or 'mouvements'  in sous: MouvementCaisse.objects.all().delete()
    if tout or 'prelevements'in sous: PrelevementBanque.objects.all().delete()
    if tout or 'sessions'    in sous: CaisseSession.objects.all().delete()


def _reset_hotel(sous=None):
    from hotel.models import Consommation, Reservation, Chambre
    tout = sous is None
    if tout or 'consommations'in sous: Consommation.objects.all().delete()
    if tout or 'reservations' in sous:
        Reservation.objects.all().delete()
        Chambre.objects.all().update(statut='disponible')
    if tout or 'clients'      in sous:
        from hotel.models import Client as HC
        HC.objects.all().delete()


def _reset_restaurant(sous=None):
    from restaurant.models import LigneCommande, Commande, Table
    LigneCommande.objects.all().delete()
    Commande.objects.all().delete()
    Table.objects.all().update(statut='libre')


def _reset_cave(sous=None):
    from bar.models import (LigneCasseBar, CasseBar, LigneInventaireBar, InventaireBar,
                            LigneBonReceptionBar, BonReceptionBar, LigneBonCommandeBar,
                            BonCommandeBar, MouvementStockBar, BoissonBar)
    tout = sous is None
    if tout or 'casses'     in sous: LigneCasseBar.objects.all().delete();      CasseBar.objects.all().delete()
    if tout or 'inventaires'in sous: LigneInventaireBar.objects.all().delete();  InventaireBar.objects.all().delete()
    if tout or 'receptions' in sous: LigneBonReceptionBar.objects.all().delete();BonReceptionBar.objects.all().delete()
    if tout or 'commandes'  in sous: LigneBonCommandeBar.objects.all().delete(); BonCommandeBar.objects.all().delete()
    if tout or 'mouvements' in sous: MouvementStockBar.objects.all().delete()
    if tout or 'stocks'     in sous: BoissonBar.objects.all().update(quantite_stock=0)


def _reset_cuisine(sous=None):
    from cuisine.models import (LigneCasseCuisine, CasseCuisine, LigneInventaireCuisine,
                                InventaireCuisine, LigneBonReceptionCuisine, BonReceptionCuisine,
                                LigneBonCommandeCuisine, BonCommandeCuisine, MouvementStockCuisine,
                                Ingredient)
    tout = sous is None
    if tout or 'casses'     in sous: LigneCasseCuisine.objects.all().delete();      CasseCuisine.objects.all().delete()
    if tout or 'inventaires'in sous: LigneInventaireCuisine.objects.all().delete();  InventaireCuisine.objects.all().delete()
    if tout or 'receptions' in sous: LigneBonReceptionCuisine.objects.all().delete();BonReceptionCuisine.objects.all().delete()
    if tout or 'commandes'  in sous: LigneBonCommandeCuisine.objects.all().delete(); BonCommandeCuisine.objects.all().delete()
    if tout or 'mouvements' in sous: MouvementStockCuisine.objects.all().delete()
    if tout or 'stocks'     in sous: Ingredient.objects.all().update(quantite_stock=0)


def _reset_piscine(sous=None):
    from piscine.models import ConsommationPiscine, AccesPiscine
    tout = sous is None
    if tout or 'consommations'in sous: ConsommationPiscine.objects.all().delete()
    if tout or 'acces'        in sous: AccesPiscine.objects.all().delete()


def _reset_espaces(sous=None):
    from espaces_evenementiels.models import ReservationEspace
    ReservationEspace.objects.all().delete()


# ── Fonctions principales ──────────────────────────────────────────────────────

def reset_modules(selection):
    """
    Reset sélectif : selection = dict {module: [sous_modules]} ou {module: True}
    Exemple:
        {'facturation': ['tickets','factures'], 'caisse': True, 'hotel': ['reservations']}
    """
    with transaction.atomic():
        for module, sous in selection.items():
            sous_list = None if sous is True else (list(sous) if sous else None)
            if module == 'facturation': _reset_facturation(sous_list)
            elif module == 'caisse':    _reset_caisse(sous_list)
            elif module == 'hotel':     _reset_hotel(sous_list)
            elif module == 'restaurant':_reset_restaurant(sous_list)
            elif module == 'cave':      _reset_cave(sous_list)
            elif module == 'cuisine':   _reset_cuisine(sous_list)
            elif module == 'piscine':   _reset_piscine(sous_list)
            elif module == 'espaces':   _reset_espaces(sous_list)
    return True


def reset_partiel():
    """Remise à zéro partielle standard — tous les modules, stocks conservés."""
    selection = {
        'facturation': True,
        'caisse':      True,
        'hotel':       True,
        'restaurant':  True,
        'cave':        ['mouvements','commandes','receptions','inventaires','casses'],
        'cuisine':     ['mouvements','commandes','receptions','inventaires','casses'],
        'piscine':     True,
        'espaces':     True,
    }
    return reset_modules(selection)


def reset_complet():
    """Remise à zéro complète — tout supprimé, stocks remis à 0."""
    selection = {mod: True for mod in MODULES}
    return reset_modules(selection)
