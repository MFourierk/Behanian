"""
Logique de remise à zéro modulaire — BEHANIAN ERP
=================================================
Deux niveaux :
  • Partielle   : supprime les transactions, conserve le référentiel (articles,
                  utilisateurs, plats, boissons, chambres, etc.) et les stocks.
  • Totale      : efface tout sauf l'infrastructure physique (chambres, tables,
                  espaces) et les comptes superuser. Réservée à l'admin Django.

Chaque module peut être sélectionné indépendamment pour la remise personnalisée.
"""

import json
import os
import logging
from io import StringIO
from django.db import transaction, connection
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


# ── Définition des modules (données transactionnelles) ────────────────────────

MODULES = {
    'facturation': {
        'label': 'Facturation',
        'color': '#1D4ED8',
        'light': '#EFF6FF',
        'icon':  '📄',
        'description': 'Tickets, Factures, Proformas, Avoirs, Clients facturation',
        'sous_modules': {
            'tickets':   'Tickets encaissement (TC-)',
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
        'icon':  '💰',
        'description': 'Sessions de caisse, Mouvements, Prélèvements banque',
        'sous_modules': {
            'sessions':     'Sessions de caisse',
            'mouvements':   'Mouvements de caisse',
            'prelevements': 'Prélèvements banque',
        },
    },
    'hotel': {
        'label': 'Hôtel',
        'color': '#2563EB',
        'light': '#DBEAFE',
        'icon':  '🏨',
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
        'icon':  '🍽️',
        'description': 'Commandes, Réservations tables, Souscriptions menus VIP',
        'sous_modules': {
            'commandes':     'Commandes + Lignes',
            'reservations':  'Réservations de tables',
            'souscriptions': 'Souscriptions Menus VIP',
        },
    },
    'cave': {
        'label': 'Cave / Bar',
        'color': '#7C3AED',
        'light': '#F5F3FF',
        'icon':  '🍷',
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
        'icon':  '👨‍🍳',
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
        'icon':  '🏊',
        'description': 'Accès / Tickets entrée, Consommations piscine',
        'sous_modules': {
            'acces':        'Accès / Tickets entrée',
            'consommations': 'Consommations piscine',
        },
    },
    'espaces': {
        'label': 'Espaces Événementiels',
        'color': '#16A085',
        'light': '#F0FDF4',
        'icon':  '📅',
        'description': 'Réservations d\'espaces événementiels',
        'sous_modules': {
            'reservations': 'Réservations espaces',
        },
    },
    'boite_nuit': {
        'label': 'Boîte de Nuit',
        'color': '#4B0082',
        'light': '#F3E8FF',
        'icon':  '🌙',
        'description': 'Entrées boîte de nuit, Consommations sur table',
        'sous_modules': {
            'entrees':      'Entrées boîte de nuit',
            'consommations': 'Consommations boîte',
        },
    },
}


# ── Comptages ─────────────────────────────────────────────────────────────────

def get_counts():
    """
    Inventaire détaillé de toutes les données transactionnelles.
    Retourne un dict imbriqué {module: {sous_module: int}}.
    """
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
        counts['facturation'] = {k: 0 for k in MODULES['facturation']['sous_modules']}

    try:
        from caisse.models import CaisseSession, MouvementCaisse, PrelevementBanque
        counts['caisse'] = {
            'sessions':     CaisseSession.objects.count(),
            'mouvements':   MouvementCaisse.objects.count(),
            'prelevements': PrelevementBanque.objects.count(),
        }
    except Exception:
        counts['caisse'] = {k: 0 for k in MODULES['caisse']['sous_modules']}

    try:
        from hotel.models import Reservation, Consommation, Client as HC
        counts['hotel'] = {
            'reservations':  Reservation.objects.count(),
            'consommations': Consommation.objects.count(),
            'clients':       HC.objects.count(),
        }
    except Exception:
        counts['hotel'] = {k: 0 for k in MODULES['hotel']['sous_modules']}

    try:
        from restaurant.models import Commande, LigneCommande, Reservation as RR, SouscriptionForfait
        counts['restaurant'] = {
            'commandes':     Commande.objects.count(),
            'reservations':  RR.objects.count(),
            'souscriptions': SouscriptionForfait.objects.count(),
        }
    except Exception:
        counts['restaurant'] = {k: 0 for k in MODULES['restaurant']['sous_modules']}

    try:
        from bar.models import (MouvementStockBar, BonCommandeBar, BonReceptionBar,
                                InventaireBar, CasseBar, BoissonBar)
        counts['cave'] = {
            'mouvements':  MouvementStockBar.objects.count(),
            'commandes':   BonCommandeBar.objects.count(),
            'receptions':  BonReceptionBar.objects.count(),
            'inventaires': InventaireBar.objects.count(),
            'casses':      CasseBar.objects.count(),
            'stocks':      BoissonBar.objects.filter(quantite_stock__gt=0).count(),
        }
    except Exception:
        counts['cave'] = {k: 0 for k in MODULES['cave']['sous_modules']}

    try:
        from cuisine.models import (MouvementStockCuisine, BonCommandeCuisine,
                                    BonReceptionCuisine, InventaireCuisine,
                                    CasseCuisine, Ingredient)
        counts['cuisine'] = {
            'mouvements':  MouvementStockCuisine.objects.count(),
            'commandes':   BonCommandeCuisine.objects.count(),
            'receptions':  BonReceptionCuisine.objects.count(),
            'inventaires': InventaireCuisine.objects.count(),
            'casses':      CasseCuisine.objects.count(),
            'stocks':      Ingredient.objects.filter(quantite_stock__gt=0).count(),
        }
    except Exception:
        counts['cuisine'] = {k: 0 for k in MODULES['cuisine']['sous_modules']}

    try:
        from piscine.models import AccesPiscine, ConsommationPiscine
        counts['piscine'] = {
            'acces':        AccesPiscine.objects.count(),
            'consommations': ConsommationPiscine.objects.count(),
        }
    except Exception:
        counts['piscine'] = {k: 0 for k in MODULES['piscine']['sous_modules']}

    try:
        from espaces_evenementiels.models import ReservationEspace
        counts['espaces'] = {
            'reservations': ReservationEspace.objects.count(),
        }
    except Exception:
        counts['espaces'] = {k: 0 for k in MODULES['espaces']['sous_modules']}

    try:
        from boite_nuit.models import EntreeBoite, ConsommationBoite
        counts['boite_nuit'] = {
            'entrees':       EntreeBoite.objects.count(),
            'consommations': ConsommationBoite.objects.count(),
        }
    except Exception:
        counts['boite_nuit'] = {k: 0 for k in MODULES['boite_nuit']['sous_modules']}

    return counts


def get_total(counts):
    """Total de toutes les transactions (hors compteurs de stock)."""
    return sum(
        v for mod in counts.values()
        for k, v in (mod.items() if isinstance(mod, dict) else {}.items())
        if isinstance(v, int) and k != 'stocks'
    )


def get_counts_json(counts):
    """Sérialiser les counts en JSON pour injection dans les templates JS."""
    return json.dumps(counts)


# ── Remise des séquences (compteurs auto-increment) ───────────────────────────

# Tables transactionnelles dont on remet le compteur à 1 après reset
SEQUENCE_TABLES = [
    # Facturation
    'facturation_ticket',
    'facturation_facture',
    'facturation_lignefacture',
    'facturation_proforma',
    'facturation_ligneproforma',
    'facturation_avoir',
    'facturation_ligneavoir',
    # Caisse
    'caisse_caissesession',
    'caisse_mouvementcaisse',
    'caisse_prelevementbanque',
    # Hôtel
    'hotel_reservation',
    'hotel_consommation',
    # Restaurant
    'restaurant_commande',
    'restaurant_lignecommande',
    'restaurant_reservation',
    'restaurant_souscriptionforfait',
    # Cave / Bar
    'bar_mouvementstockbar',
    'bar_boncommandebar',
    'bar_ligneboncommandebar',
    'bar_bonreceptionbar',
    'bar_lignebonreceptionbar',
    'bar_inventairebar',
    'bar_ligneinventairebar',
    'bar_cassebar',
    'bar_lignecassebar',
    # Cuisine
    'cuisine_mouvementstockcuisine',
    'cuisine_boncommandecuisine',
    'cuisine_ligneboncommandecuisine',
    'cuisine_bonreceptioncuisine',
    'cuisine_lignebonreceptioncuisine',
    'cuisine_inventairecuisine',
    'cuisine_ligneinventairecuisine',
    'cuisine_cassecuisine',
    'cuisine_lignecassecuisine',
    # Piscine
    'piscine_accespiscine',
    'piscine_consommationpiscine',
    # Espaces
    'espaces_evenementiels_reservationespace',
    # Boîte de nuit
    'boite_nuit_entreeboite',
    'boite_nuit_consommationboite',
]


def reset_sequences(tables=None):
    """
    Remet les compteurs auto-increment à 0 pour les tables spécifiées.
    Compatible SQLite, PostgreSQL et MySQL.
    """
    target = tables or SEQUENCE_TABLES
    vendor = connection.vendor  # 'sqlite', 'postgresql', 'mysql'

    with connection.cursor() as cursor:
        for table in target:
            try:
                if vendor == 'sqlite':
                    cursor.execute(
                        "DELETE FROM sqlite_sequence WHERE name = %s", [table]
                    )
                elif vendor == 'postgresql':
                    # Vérifie si la table existe avant de réinitialiser la séquence
                    cursor.execute(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                        "WHERE table_name = %s)", [table]
                    )
                    if cursor.fetchone()[0]:
                        cursor.execute(
                            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false)"
                        )
                elif vendor == 'mysql':
                    cursor.execute(f"ALTER TABLE `{table}` AUTO_INCREMENT = 1")
            except Exception as e:
                # La table peut ne pas avoir de séquence (ex. UUID PK)
                logger.debug("reset_sequences: %s → ignoré (%s)", table, e)


# ── Backup JSON avant reset ───────────────────────────────────────────────────

def backup_json(type_reset, user=None):
    """
    Exporte toutes les données transactionnelles en JSON.
    Enregistre dans MEDIA_ROOT/backups/reset_YYYYMMDD_HHMMSS.json.
    Retourne le chemin du fichier créé (str) ou '' en cas d'échec.
    """
    from django.core.management import call_command

    try:
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        ts       = timezone.now().strftime('%Y%m%d_%H%M%S')
        username = getattr(user, 'username', 'system')
        filename = f'reset_{type_reset}_{username}_{ts}.json'
        filepath = os.path.join(backup_dir, filename)

        out = StringIO()
        call_command(
            'dumpdata',
            'facturation', 'caisse', 'hotel', 'restaurant',
            'bar', 'cuisine', 'piscine', 'espaces_evenementiels',
            'boite_nuit',
            indent=2,
            stdout=out,
            verbosity=0,
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(out.getvalue())

        logger.info("Backup reset enregistré : %s", filepath)
        return filepath

    except Exception as e:
        logger.error("Échec backup reset : %s", e)
        return ''


# ── Journal d'audit ───────────────────────────────────────────────────────────

def journal_reset(type_reset, user, modules_selection, counts_avant, backup_path='', succes=True, erreur=''):
    """Enregistre l'opération de reset dans le journal."""
    try:
        from dashboard.models import JournalReset
        JournalReset.objects.create(
            utilisateur  = user,
            type_reset   = type_reset,
            modules      = modules_selection,
            counts_avant = counts_avant,
            backup_path  = backup_path,
            succes       = succes,
            erreur       = erreur,
        )
    except Exception as e:
        logger.error("Impossible d'écrire dans le journal : %s", e)


# ── Suppressions unitaires par module ─────────────────────────────────────────

def _reset_facturation(sous=None):
    from facturation.models import (LigneAvoir, Avoir, LigneFacture, Facture,
                                    LigneProforma, Proforma, Ticket, Client)
    tout = sous is None
    if tout or 'avoirs'    in sous: LigneAvoir.objects.all().delete();   Avoir.objects.all().delete()
    if tout or 'factures'  in sous: LigneFacture.objects.all().delete();  Facture.objects.all().delete()
    if tout or 'proformas' in sous: LigneProforma.objects.all().delete(); Proforma.objects.all().delete()
    if tout or 'tickets'   in sous: Ticket.objects.all().delete()
    if tout or 'clients'   in sous: Client.objects.all().delete()


def _reset_caisse(sous=None):
    from caisse.models import MouvementCaisse, PrelevementBanque, CaisseSession
    tout = sous is None
    if tout or 'mouvements'   in sous: MouvementCaisse.objects.all().delete()
    if tout or 'prelevements' in sous: PrelevementBanque.objects.all().delete()
    if tout or 'sessions'     in sous: CaisseSession.objects.all().delete()


def _reset_hotel(sous=None):
    from hotel.models import Consommation, Reservation, Chambre, Client as HC
    tout = sous is None
    if tout or 'consommations' in sous: Consommation.objects.all().delete()
    if tout or 'reservations'  in sous:
        Reservation.objects.all().delete()
        Chambre.objects.all().update(statut='disponible')
    if tout or 'clients'       in sous: HC.objects.all().delete()


def _reset_restaurant(sous=None):
    from restaurant.models import LigneCommande, Commande, Table, Reservation as RR, SouscriptionForfait
    tout = sous is None
    if tout or 'commandes'     in sous:
        LigneCommande.objects.all().delete()
        Commande.objects.all().delete()
        Table.objects.all().update(statut='libre')
    if tout or 'reservations'  in sous: RR.objects.all().delete()
    if tout or 'souscriptions' in sous: SouscriptionForfait.objects.all().delete()


def _reset_cave(sous=None):
    from bar.models import (LigneCasseBar, CasseBar, LigneInventaireBar, InventaireBar,
                            LigneBonReceptionBar, BonReceptionBar, LigneBonCommandeBar,
                            BonCommandeBar, MouvementStockBar, BoissonBar)
    tout = sous is None
    if tout or 'casses'      in sous: LigneCasseBar.objects.all().delete();       CasseBar.objects.all().delete()
    if tout or 'inventaires' in sous: LigneInventaireBar.objects.all().delete();   InventaireBar.objects.all().delete()
    if tout or 'receptions'  in sous: LigneBonReceptionBar.objects.all().delete(); BonReceptionBar.objects.all().delete()
    if tout or 'commandes'   in sous: LigneBonCommandeBar.objects.all().delete();  BonCommandeBar.objects.all().delete()
    if tout or 'mouvements'  in sous: MouvementStockBar.objects.all().delete()
    if tout or 'stocks'      in sous: BoissonBar.objects.all().update(quantite_stock=0)


def _reset_cuisine(sous=None):
    from cuisine.models import (LigneCasseCuisine, CasseCuisine, LigneInventaireCuisine,
                                InventaireCuisine, LigneBonReceptionCuisine, BonReceptionCuisine,
                                LigneBonCommandeCuisine, BonCommandeCuisine,
                                MouvementStockCuisine, Ingredient)
    tout = sous is None
    if tout or 'casses'      in sous: LigneCasseCuisine.objects.all().delete();       CasseCuisine.objects.all().delete()
    if tout or 'inventaires' in sous: LigneInventaireCuisine.objects.all().delete();   InventaireCuisine.objects.all().delete()
    if tout or 'receptions'  in sous: LigneBonReceptionCuisine.objects.all().delete(); BonReceptionCuisine.objects.all().delete()
    if tout or 'commandes'   in sous: LigneBonCommandeCuisine.objects.all().delete();  BonCommandeCuisine.objects.all().delete()
    if tout or 'mouvements'  in sous: MouvementStockCuisine.objects.all().delete()
    if tout or 'stocks'      in sous:
        # Reset stock ET coût moyen unitaire pondéré
        Ingredient.objects.all().update(quantite_stock=0, cmup=0)


def _reset_piscine(sous=None):
    from piscine.models import ConsommationPiscine, AccesPiscine
    tout = sous is None
    if tout or 'consommations' in sous: ConsommationPiscine.objects.all().delete()
    if tout or 'acces'         in sous: AccesPiscine.objects.all().delete()


def _reset_espaces(sous=None):
    from espaces_evenementiels.models import ReservationEspace, EspaceEvenementiel
    ReservationEspace.objects.all().delete()
    EspaceEvenementiel.objects.all().update(statut='disponible')


def _reset_boite_nuit(sous=None):
    from boite_nuit.models import EntreeBoite, ConsommationBoite, TableBoite
    tout = sous is None
    if tout or 'consommations' in sous:
        ConsommationBoite.objects.all().delete()
        TableBoite.objects.all().update(statut='disponible')
    if tout or 'entrees'       in sous: EntreeBoite.objects.all().delete()


# ── Fonction principale : reset sélectif ──────────────────────────────────────

def reset_modules(selection):
    """
    Reset sélectif atomique.
    selection = dict {module: [sous_modules]} ou {module: True}

    Exemple :
        {'facturation': ['tickets', 'factures'], 'caisse': True}
    """
    with transaction.atomic():
        for module, sous in selection.items():
            sous_list = None if sous is True else (list(sous) if sous else None)
            if   module == 'facturation': _reset_facturation(sous_list)
            elif module == 'caisse':      _reset_caisse(sous_list)
            elif module == 'hotel':       _reset_hotel(sous_list)
            elif module == 'restaurant':  _reset_restaurant(sous_list)
            elif module == 'cave':        _reset_cave(sous_list)
            elif module == 'cuisine':     _reset_cuisine(sous_list)
            elif module == 'piscine':     _reset_piscine(sous_list)
            elif module == 'espaces':     _reset_espaces(sous_list)
            elif module == 'boite_nuit':  _reset_boite_nuit(sous_list)

        # Remise des compteurs à 0 après toute suppression
        reset_sequences()

    return True


# ── Remise Partielle (standard) ───────────────────────────────────────────────

def reset_partiel(user=None):
    """
    Supprime toutes les transactions de tous les modules.
    Conserve : utilisateurs, référentiel (articles, plats, boissons,
               ingrédients, fiches techniques, chambres, tables, etc.)
               et les niveaux de stock actuels.
    Remet les compteurs à 0.
    """
    counts_avant = get_counts()
    backup_path  = backup_json('partiel', user)

    selection = {
        'facturation': True,
        'caisse':      True,
        'hotel':       True,
        'restaurant':  True,
        'cave':        ['mouvements', 'commandes', 'receptions', 'inventaires', 'casses'],
        'cuisine':     ['mouvements', 'commandes', 'receptions', 'inventaires', 'casses'],
        'piscine':     True,
        'espaces':     True,
        'boite_nuit':  True,
    }

    try:
        reset_modules(selection)
        journal_reset('partiel', user, selection, counts_avant, backup_path, succes=True)
        return True, backup_path
    except Exception as e:
        journal_reset('partiel', user, selection, counts_avant, backup_path, succes=False, erreur=str(e))
        raise


# ── Remise Stocks (mouvements effacés + quantités à 0, articles conservés) ───

def reset_stocks(user=None):
    """
    Remet à zéro les mouvements ET les quantités de stock.
    Conserve : utilisateurs, référentiel complet (articles, boissons, ingrédients,
               plats, fiches techniques, tarifs, chambres, tables…) et leurs prix.
    Supprime  : BC, BR, mouvements, inventaires, casses pour Cave et Cuisine.
                Transactions de tous les autres modules (commandes, réservations,
                tickets, sessions caisse…).
    Remet     : quantite_stock → 0 pour BoissonBar et Ingredient.
                cmup → 0 pour Ingredient.
    """
    counts_avant = get_counts()
    backup_path  = backup_json('stocks', user)

    selection = {
        'facturation': True,
        'caisse':      True,
        'hotel':       True,
        'restaurant':  True,
        'cave':        ['mouvements', 'commandes', 'receptions', 'inventaires', 'casses', 'stocks'],
        'cuisine':     ['mouvements', 'commandes', 'receptions', 'inventaires', 'casses', 'stocks'],
        'piscine':     True,
        'espaces':     True,
        'boite_nuit':  True,
    }

    try:
        reset_modules(selection)
        journal_reset('stocks', user, selection, counts_avant, backup_path, succes=True)
        return True, backup_path
    except Exception as e:
        journal_reset('stocks', user, selection, counts_avant, backup_path, succes=False, erreur=str(e))
        raise


# ── Remise Totale (admin Django uniquement) ───────────────────────────────────

def reset_complet(user=None):
    """
    Remise à zéro totale — RÉSERVÉE À L'ADMIN DJANGO.

    Efface :
      • Toutes les transactions (même périmètre que partielle)
      • Tous les stocks (boissons + ingrédients remis à 0)
      • Tous les éléments du référentiel : articles, plats, boissons,
        ingrédients, fiches techniques, catégories, clients, fournisseurs,
        forfaits, événements boîte de nuit
      • Tous les utilisateurs SAUF les comptes superuser

    Conserve (infrastructure physique du complexe) :
      • Chambres (hotel.Chambre) — avec statut remis à 'disponible'
      • Tables restaurant (restaurant.Table) — statut 'libre'
      • Tables bar (bar.TableBar) — statut 'libre'
      • Tables boîte de nuit (boite_nuit.TableBoite) — statut 'disponible'
      • Espaces événementiels (espaces_evenementiels.EspaceEvenementiel) — statut 'disponible'
      • Tarifs piscine (piscine.TarifPiscine)
      • Configuration du complexe (dashboard.Configuration) — singleton indestructible
    """
    counts_avant = get_counts()
    backup_path  = backup_json('complet', user)

    try:
        with transaction.atomic():

            # 1. Toutes les transactions + stocks
            for mod in MODULES:
                sous_list = list(MODULES[mod]['sous_modules'].keys())
                if   mod == 'facturation': _reset_facturation(sous_list)
                elif mod == 'caisse':      _reset_caisse(sous_list)
                elif mod == 'hotel':       _reset_hotel(sous_list)
                elif mod == 'restaurant':  _reset_restaurant(sous_list)
                elif mod == 'cave':        _reset_cave(sous_list)
                elif mod == 'cuisine':     _reset_cuisine(sous_list)
                elif mod == 'piscine':     _reset_piscine(sous_list)
                elif mod == 'espaces':     _reset_espaces(sous_list)
                elif mod == 'boite_nuit':  _reset_boite_nuit(sous_list)

            # 2. Référentiel bar
            from bar.models import BoissonBar, CategorieBar, Client as BarClient
            BoissonBar.objects.all().delete()
            CategorieBar.objects.all().delete()
            BarClient.objects.all().delete()

            # 3. Référentiel cuisine
            from cuisine.models import (Plat, LigneFicheTechnique, FicheTechnique,
                                        Ingredient, CategorieIngredient, UniteIngredient,
                                        CategoriePlat, Fournisseur)
            Plat.objects.all().delete()
            LigneFicheTechnique.objects.all().delete()
            FicheTechnique.objects.all().delete()
            Ingredient.objects.all().delete()
            CategorieIngredient.objects.all().delete()
            UniteIngredient.objects.all().delete()
            CategoriePlat.objects.all().delete()
            Fournisseur.objects.all().delete()

            # 4. Référentiel restaurant (menu + forfaits)
            from restaurant.models import LigneForfait, Forfait, PlatMenu, CategorieMenu
            LigneForfait.objects.all().delete()
            Forfait.objects.all().delete()
            PlatMenu.objects.all().delete()
            CategorieMenu.objects.all().delete()

            # 5. Référentiel facturation
            from facturation.models import Article as FacArticle, Service as FacService
            FacArticle.objects.all().delete()
            FacService.objects.all().delete()

            # 6. Boîte de nuit — événements
            from boite_nuit.models import Evenement
            Evenement.objects.all().delete()

            # 7. Utilisateurs non-superuser
            from django.contrib.auth.models import User
            User.objects.filter(is_superuser=False).delete()

            # 8. Remise des compteurs à 0 (toutes les tables transactionnelles + référentielles)
            reset_sequences()

        selection = {mod: list(MODULES[mod]['sous_modules'].keys()) for mod in MODULES}
        selection['_referentiel'] = 'complet'
        journal_reset('complet', user, selection, counts_avant, backup_path, succes=True)
        return True, backup_path

    except Exception as e:
        journal_reset('complet', user, {}, counts_avant, backup_path, succes=False, erreur=str(e))
        raise
