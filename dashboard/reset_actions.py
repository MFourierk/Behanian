"""
Logique de remise à zéro — BEHANIAN
Appelée depuis les vues admin personnalisées.
"""
from django.db import transaction


def get_counts():
    """Inventaire de toutes les transactions actuelles."""
    counts = {}

    # Facturation
    try:
        from facturation.models import Ticket, Facture, LigneFacture, Proforma, LigneProforma, Avoir, LigneAvoir, Client
        counts['facturation'] = {
            'Tickets':            Ticket.objects.count(),
            'Factures':           Facture.objects.count(),
            'Proformas':          Proforma.objects.count(),
            'Avoirs':             Avoir.objects.count(),
            'Clients facturation':Client.objects.count(),
        }
    except Exception as e:
        counts['facturation'] = {'erreur': str(e)}

    # Caisse
    try:
        from caisse.models import CaisseSession, MouvementCaisse, PrelevementBanque
        counts['caisse'] = {
            'Sessions caisse':    CaisseSession.objects.count(),
            'Mouvements caisse':  MouvementCaisse.objects.count(),
            'Prélèvements banque':PrelevementBanque.objects.count(),
        }
    except Exception as e:
        counts['caisse'] = {'erreur': str(e)}

    # Hôtel
    try:
        from hotel.models import Reservation, Consommation, Client as HotelClient
        counts['hotel'] = {
            'Réservations hôtel': Reservation.objects.count(),
            'Consommations hôtel':Consommation.objects.count(),
            'Clients hôtel':      HotelClient.objects.count(),
        }
    except Exception as e:
        counts['hotel'] = {'erreur': str(e)}

    # Restaurant
    try:
        from restaurant.models import Commande, LigneCommande
        counts['restaurant'] = {
            'Commandes restaurant':Commande.objects.count(),
            'Lignes commande':     LigneCommande.objects.count(),
        }
    except Exception as e:
        counts['restaurant'] = {'erreur': str(e)}

    # Cave / Bar
    try:
        from bar.models import MouvementStockBar, BonCommandeBar, BonReceptionBar, InventaireBar, CasseBar
        counts['cave'] = {
            'Mouvements stock cave':MouvementStockBar.objects.count(),
            'Bons commande cave':   BonCommandeBar.objects.count(),
            'Bons réception cave':  BonReceptionBar.objects.count(),
            'Inventaires cave':     InventaireBar.objects.count(),
            'Casses cave':          CasseBar.objects.count(),
        }
    except Exception as e:
        counts['cave'] = {'erreur': str(e)}

    # Cuisine
    try:
        from cuisine.models import MouvementStockCuisine, BonCommandeCuisine, BonReceptionCuisine, InventaireCuisine, CasseCuisine
        counts['cuisine'] = {
            'Mouvements stock cuisine':MouvementStockCuisine.objects.count(),
            'Bons commande cuisine':   BonCommandeCuisine.objects.count(),
            'Bons réception cuisine':  BonReceptionCuisine.objects.count(),
            'Inventaires cuisine':     InventaireCuisine.objects.count(),
            'Casses cuisine':          CasseCuisine.objects.count(),
        }
    except Exception as e:
        counts['cuisine'] = {'erreur': str(e)}

    # Piscine
    try:
        from piscine.models import AccesPiscine, ConsommationPiscine
        counts['piscine'] = {
            'Accès piscine':          AccesPiscine.objects.count(),
            'Consommations piscine':  ConsommationPiscine.objects.count(),
        }
    except Exception as e:
        counts['piscine'] = {'erreur': str(e)}

    # Espaces
    try:
        from espaces_evenementiels.models import ReservationEspace
        counts['espaces'] = {
            'Réservations espaces':   ReservationEspace.objects.count(),
        }
    except Exception as e:
        counts['espaces'] = {'erreur': str(e)}

    return counts


def _supprimer_facturation():
    from facturation.models import (LigneAvoir, Avoir, LigneFacture, Facture,
                                    LigneProforma, Proforma, Ticket, Client)
    LigneAvoir.objects.all().delete()
    Avoir.objects.all().delete()
    LigneFacture.objects.all().delete()
    Facture.objects.all().delete()
    LigneProforma.objects.all().delete()
    Proforma.objects.all().delete()
    Ticket.objects.all().delete()
    Client.objects.all().delete()


def _supprimer_caisse():
    from caisse.models import MouvementCaisse, PrelevementBanque, CaisseSession
    MouvementCaisse.objects.all().delete()
    PrelevementBanque.objects.all().delete()
    CaisseSession.objects.all().delete()


def _supprimer_hotel(avec_clients=True):
    from hotel.models import Consommation, Reservation, Chambre
    Consommation.objects.all().delete()
    Reservation.objects.all().delete()
    Chambre.objects.all().update(statut='disponible')
    if avec_clients:
        from hotel.models import Client as HotelClient
        HotelClient.objects.all().delete()


def _supprimer_restaurant():
    from restaurant.models import LigneCommande, Commande, Table
    LigneCommande.objects.all().delete()
    Commande.objects.all().delete()
    Table.objects.all().update(statut='libre')


def _supprimer_cave(reset_stock=False):
    from bar.models import (LigneCasseBar, CasseBar, LigneInventaireBar, InventaireBar,
                            LigneBonReceptionBar, BonReceptionBar, LigneBonCommandeBar,
                            BonCommandeBar, MouvementStockBar)
    LigneCasseBar.objects.all().delete()
    CasseBar.objects.all().delete()
    LigneInventaireBar.objects.all().delete()
    InventaireBar.objects.all().delete()
    LigneBonReceptionBar.objects.all().delete()
    BonReceptionBar.objects.all().delete()
    LigneBonCommandeBar.objects.all().delete()
    BonCommandeBar.objects.all().delete()
    MouvementStockBar.objects.all().delete()
    if reset_stock:
        from bar.models import BoissonBar
        BoissonBar.objects.all().update(quantite_stock=0)


def _supprimer_cuisine(reset_stock=False):
    from cuisine.models import (LigneCasseCuisine, CasseCuisine, LigneInventaireCuisine,
                                InventaireCuisine, LigneBonReceptionCuisine, BonReceptionCuisine,
                                LigneBonCommandeCuisine, BonCommandeCuisine, MouvementStockCuisine,
                                Ingredient)
    LigneCasseCuisine.objects.all().delete()
    CasseCuisine.objects.all().delete()
    LigneInventaireCuisine.objects.all().delete()
    InventaireCuisine.objects.all().delete()
    LigneBonReceptionCuisine.objects.all().delete()
    BonReceptionCuisine.objects.all().delete()
    LigneBonCommandeCuisine.objects.all().delete()
    BonCommandeCuisine.objects.all().delete()
    MouvementStockCuisine.objects.all().delete()
    if reset_stock:
        Ingredient.objects.all().update(quantite_stock=0)


def _supprimer_piscine():
    from piscine.models import ConsommationPiscine, AccesPiscine
    ConsommationPiscine.objects.all().delete()
    AccesPiscine.objects.all().delete()


def _supprimer_espaces():
    from espaces_evenementiels.models import ReservationEspace
    ReservationEspace.objects.all().delete()


def reset_partiel():
    """
    REMISE À ZÉRO PARTIELLE
    Supprime toutes les transactions et réinitialise les numérotations.
    Conserve : articles, plats, boissons (avec stocks), chambres, espaces,
               tables, catégories, ingrédients (avec stocks), tarifs, utilisateurs.
    """
    with transaction.atomic():
        _supprimer_facturation()
        _supprimer_caisse()
        _supprimer_hotel(avec_clients=True)
        _supprimer_restaurant()
        _supprimer_cave(reset_stock=False)   # garde les stocks cave
        _supprimer_cuisine(reset_stock=False) # garde les stocks cuisine
        _supprimer_piscine()
        _supprimer_espaces()
    return True


def reset_complet():
    """
    REMISE À ZÉRO COMPLÈTE
    Tout ce que fait la partielle + remet les stocks à 0.
    Conserve UNIQUEMENT la structure : catégories, types, tables, chambres,
    espaces, plats, boissons, ingrédients (quantité=0), utilisateurs, groupes, tarifs.
    """
    with transaction.atomic():
        _supprimer_facturation()
        _supprimer_caisse()
        _supprimer_hotel(avec_clients=True)
        _supprimer_restaurant()
        _supprimer_cave(reset_stock=True)    # remet stocks cave à 0
        _supprimer_cuisine(reset_stock=True)  # remet stocks cuisine à 0
        _supprimer_piscine()
        _supprimer_espaces()
    return True
