"""
Commande de remise à zéro pour nouveau départ.

CONSERVÉ : utilisateurs, articles/boissons/ingrédients (config + CMUP + prix),
           clients hôtel, tarifs hôtel/piscine/espaces, carte restaurant,
           fiches techniques, paramétrage shots, fournisseurs.

REMIS À ZÉRO : quantite_stock → 0 (CMUP et prix intacts).

SUPPRIMÉ : toutes les transactions — tickets, mouvements stock, commandes,
           ventes, réservations, sessions caisse, bons réception/commande,
           inventaires passés, casses, accès piscine, consommations.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Remet tous les compteurs à zéro pour un nouveau départ (garde CMUP, prix, clients, tarifs)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== REMISE À ZÉRO — DÉBUT ==="))

        with transaction.atomic():

            # ── FACTURATION ──────────────────────────────────────────────────
            from facturation.models import Ticket, Avoir, LigneAvoir, Facture, LigneFacture, Proforma, LigneProforma
            self._supprimer("LigneAvoir",     LigneAvoir.objects.all())
            self._supprimer("Avoir",          Avoir.objects.all())
            self._supprimer("LigneFacture",   LigneFacture.objects.all())
            self._supprimer("Facture",        Facture.objects.all())
            self._supprimer("LigneProforma",  LigneProforma.objects.all())
            self._supprimer("Proforma",       Proforma.objects.all())
            self._supprimer("Ticket",         Ticket.objects.all())

            # ── RESTAURANT ───────────────────────────────────────────────────
            from restaurant.models import LigneCommande, Commande, Reservation as ReservationResto, SouscriptionForfait
            self._supprimer("LigneCommande",       LigneCommande.objects.all())
            self._supprimer("Commande restaurant", Commande.objects.all())
            self._supprimer("Réservation resto",   ReservationResto.objects.all())
            self._supprimer("SouscriptionForfait", SouscriptionForfait.objects.all())

            # ── CAVE / BAR ───────────────────────────────────────────────────
            from bar.models import (
                LigneVenteCave, VenteCave, VenteShot,
                MouvementStockBar,
                LigneBonReceptionBar, BonReceptionBar,
                LigneBonCommandeBar, BonCommandeBar,
                LigneInventaireBar, InventaireBar,
                LigneCasseBar, CasseBar,
            )
            self._supprimer("LigneVenteCave",      LigneVenteCave.objects.all())
            self._supprimer("VenteCave",            VenteCave.objects.all())
            self._supprimer("VenteShot",            VenteShot.objects.all())
            self._supprimer("MouvementStockBar",    MouvementStockBar.objects.all())
            self._supprimer("LigneBonReceptionBar", LigneBonReceptionBar.objects.all())
            self._supprimer("BonReceptionBar",      BonReceptionBar.objects.all())
            self._supprimer("LigneBonCommandeBar",  LigneBonCommandeBar.objects.all())
            self._supprimer("BonCommandeBar",       BonCommandeBar.objects.all())
            self._supprimer("LigneInventaireBar",   LigneInventaireBar.objects.all())
            self._supprimer("InventaireBar",        InventaireBar.objects.all())
            self._supprimer("LigneCasseBar",        LigneCasseBar.objects.all())
            self._supprimer("CasseBar",             CasseBar.objects.all())

            # ── CUISINE ──────────────────────────────────────────────────────
            from cuisine.models import (
                MouvementStockCuisine,
                LigneBonReceptionCuisine, BonReceptionCuisine,
                LigneBonCommandeCuisine, BonCommandeCuisine,
                LigneInventaireCuisine, InventaireCuisine,
                LigneCasseCuisine, CasseCuisine,
            )
            self._supprimer("MouvementStockCuisine",    MouvementStockCuisine.objects.all())
            self._supprimer("LigneBonReceptionCuisine", LigneBonReceptionCuisine.objects.all())
            self._supprimer("BonReceptionCuisine",      BonReceptionCuisine.objects.all())
            self._supprimer("LigneBonCommandeCuisine",  LigneBonCommandeCuisine.objects.all())
            self._supprimer("BonCommandeCuisine",       BonCommandeCuisine.objects.all())
            self._supprimer("LigneInventaireCuisine",   LigneInventaireCuisine.objects.all())
            self._supprimer("InventaireCuisine",        InventaireCuisine.objects.all())
            self._supprimer("LigneCasseCuisine",        LigneCasseCuisine.objects.all())
            self._supprimer("CasseCuisine",             CasseCuisine.objects.all())

            # ── PISCINE ──────────────────────────────────────────────────────
            from piscine.models import ConsommationPiscine, AccesPiscine
            self._supprimer("ConsommationPiscine", ConsommationPiscine.objects.all())
            self._supprimer("AccesPiscine",        AccesPiscine.objects.all())

            # ── HÔTEL ────────────────────────────────────────────────────────
            from hotel.models import Consommation as ConsommationHotel, Reservation as ReservationHotel
            self._supprimer("ConsommationHotel",   ConsommationHotel.objects.all())
            self._supprimer("ReservationHotel",    ReservationHotel.objects.all())
            # hotel.Client → GARDÉ

            # ── CAISSE ───────────────────────────────────────────────────────
            from caisse.models import MouvementCaisse, CaisseSession, PrelevementBanque
            self._supprimer("MouvementCaisse",   MouvementCaisse.objects.all())
            self._supprimer("CaisseSession",     CaisseSession.objects.all())
            self._supprimer("PrelevementBanque", PrelevementBanque.objects.all())

            # ── ESPACES ──────────────────────────────────────────────────────
            from espaces_evenementiels.models import ReservationEspace
            self._supprimer("ReservationEspace", ReservationEspace.objects.all())

            # ── STOCKS → ZÉRO (CMUP et prix intacts) ─────────────────────────
            from bar.models import BoissonBar
            from cuisine.models import Ingredient
            nb_bar = BoissonBar.objects.update(quantite_stock=0)
            self.stdout.write(f"  → BoissonBar.quantite_stock = 0  ({nb_bar} articles)")
            nb_cui = Ingredient.objects.update(quantite_stock=0)
            self.stdout.write(f"  → Ingredient.quantite_stock = 0  ({nb_cui} ingrédients)")

        self.stdout.write(self.style.SUCCESS("=== REMISE À ZÉRO — TERMINÉE AVEC SUCCÈS ==="))

    def _supprimer(self, label, qs):
        nb, _ = qs.delete()
        self.stdout.write(f"  ✓ {label} : {nb} supprimé(s)")
