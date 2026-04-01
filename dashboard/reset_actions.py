"""
Logique de remise à zéro — BEHANIAN
"""
from django.db import transaction


def get_counts():
    counts = {}
    try:
        from facturation.models import Ticket, Facture, Proforma, Avoir, Client
        counts['facturation'] = {
            'Tickets':             Ticket.objects.count(),
            'Factures':            Facture.objects.count(),
            'Proformas':           Proforma.objects.count(),
            'Avoirs':              Avoir.objects.count(),
            'Clients facturation': Client.objects.count(),
        }
    except Exception as e:
        counts['facturation'] = {'erreur': str(e)}

    try:
        from caisse.models import CaisseSession, MouvementCaisse, PrelevementBanque
        counts['caisse'] = {
            'Sessions caisse':     CaisseSession.objects.count(),
            'Mouvements caisse':   MouvementCaisse.objects.count(),
            'Prélèvements banque': PrelevementBanque.objects.count(),
        }
    except Exception as e:
        counts['caisse'] = {'erreur': str(e)}

    try:
        from hotel.models import Reservation, Consommation, Client as HotelClient
        counts['hotel'] = {
            'Réservations hôtel':  Reservation.objects.count(),
            'Consommations hôtel': Consommation.objects.count(),
            'Clients hôtel':       HotelClient.objects.count(),
        }
    except Exception as e:
        counts['hotel'] = {'erreur': str(e)}

    try:
        from restaurant.models import Commande, LigneCommande
        counts['restaurant'] = {
            'Commandes restaurant': Commande.objects.count(),
            'Lignes commande':      LigneCommande.objects.count(),
        }
    except Exception as e:
        counts['restaurant'] = {'erreur': str(e)}

    try:
        from bar.models import MouvementStockBar, BonCommandeBar, BonReceptionBar, InventaireBar, CasseBar, BoissonBar
        counts['cave'] = {
            'Mouvements stock cave': MouvementStockBar.objects.count(),
            'Bons commande cave':    BonCommandeBar.objects.count(),
            'Bons réception cave':   BonReceptionBar.objects.count(),
            'Inventaires cave':      InventaireBar.objects.count(),
            'Casses cave':           CasseBar.objects.count(),
            'Stock cave (articles)': BoissonBar.objects.count(),
        }
    except Exception as e:
        counts['cave'] = {'erreur': str(e)}

    try:
        from cuisine.models import MouvementStockCuisine, BonCommandeCuisine, BonReceptionCuisine, InventaireCuisine, CasseCuisine, Ingredient
        counts['cuisine'] = {
            'Mouvements stock cuisine': MouvementStockCuisine.objects.count(),
            'Bons commande cuisine':    BonCommandeCuisine.objects.count(),
            'Bons réception cuisine':   BonReceptionCuisine.objects.count(),
            'Inventaires cuisine':      InventaireCuisine.objects.count(),
            'Casses cuisine':           CasseCuisine.objects.count(),
            'Ingrédients (articles)':   Ingredient.objects.count(),
        }
    except Exception as e:
        counts['cuisine'] = {'erreur': str(e)}

    try:
        from piscine.models import AccesPiscine, ConsommationPiscine
        counts['piscine'] = {
            'Accès piscine':          AccesPiscine.objects.count(),
            'Consommations piscine':  ConsommationPiscine.objects.count(),
        }
    except Exception as e:
        counts['piscine'] = {'erreur': str(e)}

    try:
        from espaces_evenementiels.models import ReservationEspace
        counts['espaces'] = {
            'Réservations espaces': ReservationEspace.objects.count(),
        }
    except Exception as e:
        counts['espaces'] = {'erreur': str(e)}

    return counts


# ─────────────────────────────────────────────────────────────────────────────
#  REMISE À ZÉRO PARTIELLE
#  Supprime : toutes les transactions + documents + stocks cave et cuisine
#  Réinitialise : statuts chambres → disponible, tables → libre, espaces → disponible
#  Conserve : articles, plats, boissons, chambres, espaces, tables,
#             catégories, ingrédients (structure), tarifs, utilisateurs, groupes
# ─────────────────────────────────────────────────────────────────────────────
def reset_partiel():
    with transaction.atomic():

        # ── Facturation ──────────────────────────────────────────────────────
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

        # ── Caisse ───────────────────────────────────────────────────────────
        from caisse.models import MouvementCaisse, PrelevementBanque, CaisseSession
        MouvementCaisse.objects.all().delete()
        PrelevementBanque.objects.all().delete()
        CaisseSession.objects.all().delete()

        # ── Hôtel ─────────────────────────────────────────────────────────────
        from hotel.models import Consommation, Reservation, Chambre, Client as HotelClient
        Consommation.objects.all().delete()
        Reservation.objects.all().delete()
        HotelClient.objects.all().delete()
        Chambre.objects.all().update(statut='disponible')   # ← statut réinitialisé

        # ── Restaurant ────────────────────────────────────────────────────────
        from restaurant.models import LigneCommande, Commande, Table
        LigneCommande.objects.all().delete()
        Commande.objects.all().delete()
        Table.objects.all().update(statut='libre')           # ← statut réinitialisé

        # ── Cave / Bar ─────────────────────────────────────────────────────────
        from bar.models import (LigneCasseBar, CasseBar, LigneInventaireBar, InventaireBar,
                                LigneBonReceptionBar, BonReceptionBar, LigneBonCommandeBar,
                                BonCommandeBar, MouvementStockBar, BoissonBar)
        LigneCasseBar.objects.all().delete()
        CasseBar.objects.all().delete()
        LigneInventaireBar.objects.all().delete()
        InventaireBar.objects.all().delete()
        LigneBonReceptionBar.objects.all().delete()
        BonReceptionBar.objects.all().delete()
        LigneBonCommandeBar.objects.all().delete()
        BonCommandeBar.objects.all().delete()
        MouvementStockBar.objects.all().delete()
        BoissonBar.objects.all().update(quantite_stock=0)    # ← stocks → 0

        # ── Cuisine ───────────────────────────────────────────────────────────
        from cuisine.models import (LigneCasseCuisine, CasseCuisine, LigneInventaireCuisine,
                                    InventaireCuisine, LigneBonReceptionCuisine, BonReceptionCuisine,
                                    LigneBonCommandeCuisine, BonCommandeCuisine,
                                    MouvementStockCuisine, Ingredient)
        LigneCasseCuisine.objects.all().delete()
        CasseCuisine.objects.all().delete()
        LigneInventaireCuisine.objects.all().delete()
        InventaireCuisine.objects.all().delete()
        LigneBonReceptionCuisine.objects.all().delete()
        BonReceptionCuisine.objects.all().delete()
        LigneBonCommandeCuisine.objects.all().delete()
        BonCommandeCuisine.objects.all().delete()
        MouvementStockCuisine.objects.all().delete()
        Ingredient.objects.all().update(quantite_stock=0)    # ← stocks → 0

        # ── Piscine ───────────────────────────────────────────────────────────
        from piscine.models import ConsommationPiscine, AccesPiscine
        ConsommationPiscine.objects.all().delete()
        AccesPiscine.objects.all().delete()

        # ── Espaces ───────────────────────────────────────────────────────────
        from espaces_evenementiels.models import ReservationEspace, EspaceEvenementiel
        ReservationEspace.objects.all().delete()
        try:
            EspaceEvenementiel.objects.all().update(statut='disponible')  # ← statut réinitialisé
        except Exception:
            pass  # champ statut peut ne pas exister

    return True


# ─────────────────────────────────────────────────────────────────────────────
#  REMISE À ZÉRO COMPLÈTE
#  Tout ce que fait la partielle +
#  Supprime aussi : boissons cave, ingrédients cuisine, chambres, espaces,
#                   tables restaurant, tables cave, plats, catégories, tarifs piscine
#  Conserve UNIQUEMENT : utilisateurs, groupes, permissions
# ─────────────────────────────────────────────────────────────────────────────
def reset_complet():
    # D'abord tout ce que fait la partielle
    reset_partiel()

    with transaction.atomic():

        # ── Cave : supprimer tous les articles ───────────────────────────────
        from bar.models import BoissonBar, CategorieBar, TableBar
        BoissonBar.objects.all().delete()
        CategorieBar.objects.all().delete()
        TableBar.objects.all().delete()

        # ── Cuisine : supprimer articles et structure ────────────────────────
        from cuisine.models import (LigneFicheTechnique, FicheTechnique, Plat,
                                    CategoriePlat, Ingredient, CategorieIngredient,
                                    UniteIngredient, Fournisseur)
        LigneFicheTechnique.objects.all().delete()
        FicheTechnique.objects.all().delete()
        Plat.objects.all().delete()
        CategoriePlat.objects.all().delete()
        Ingredient.objects.all().delete()
        CategorieIngredient.objects.all().delete()
        UniteIngredient.objects.all().delete()
        Fournisseur.objects.all().delete()

        # ── Restaurant : supprimer plats, catégories, tables ─────────────────
        from restaurant.models import PlatMenu, CategorieMenu, Table
        PlatMenu.objects.all().delete()
        CategorieMenu.objects.all().delete()
        Table.objects.all().delete()

        # ── Hôtel : supprimer chambres ───────────────────────────────────────
        from hotel.models import Chambre
        Chambre.objects.all().delete()

        # ── Espaces : supprimer espaces ──────────────────────────────────────
        from espaces_evenementiels.models import EspaceEvenementiel
        EspaceEvenementiel.objects.all().delete()

        # ── Piscine : supprimer tarifs ────────────────────────────────────────
        try:
            from piscine.models import TarifPiscine
            TarifPiscine.objects.all().delete()
        except Exception:
            pass

        # ── Facturation : supprimer services et articles ──────────────────────
        try:
            from facturation.models import Service, Article
            Service.objects.all().delete()
            Article.objects.all().delete()
        except Exception:
            pass

    return True
