from decimal import Decimal
from django.db import transaction
from .models import FicheTechnique, MouvementStockCuisine, Ingredient


def _ingredient_par_nom(nom_plat):
    """Retourne le premier ingrédient actif dont le nom correspond (insensible à la casse)."""
    return Ingredient.objects.filter(nom__iexact=nom_plat, statut=True).first()


def check_stock_availability(plat, quantity=1):
    """
    Bloque uniquement en rupture totale (stock ≤ 0 sur un ingrédient).
    Stock bas (> 0 mais < quantité nécessaire) : vente autorisée.
    """
    nom_plat = getattr(plat, 'nom', 'ce plat')

    if not hasattr(plat, 'fiche_technique') or plat.fiche_technique is None:
        return True, ""

    fiche = plat.fiche_technique
    lignes = list(fiche.lignes.select_related('ingredient').all())

    if not lignes:
        ing = _ingredient_par_nom(nom_plat)
        if ing and ing.quantite_stock <= 0:
            return False, f"« {nom_plat} » en rupture de stock."
        return True, ""

    en_rupture = [l.ingredient for l in lignes if l.ingredient.quantite_stock <= 0]
    if en_rupture:
        detail = ", ".join(i.nom for i in en_rupture)
        return False, f"« {nom_plat} » — rupture : {detail}"

    return True, ""


@transaction.atomic
def process_stock_movement(plat, quantity, movement_type, user, reference=""):
    """
    Effectue les mouvements de stock pour un plat basé sur sa fiche technique.
    movement_type : 'sortie' (vente/production) ou 'entree' (annulation)

    Si la FT est vide, tente le déstockage par correspondance de nom d'ingrédient.
    """
    if not hasattr(plat, 'fiche_technique') or plat.fiche_technique is None:
        return

    fiche    = plat.fiche_technique
    type_mvt = 'production' if movement_type == 'sortie' else 'entree'
    label    = 'Production' if movement_type == 'sortie' else 'Annulation retour stock'
    lignes   = list(fiche.lignes.select_related('ingredient').all())

    if not lignes:
        # FT vide → déstockage par nom d'ingrédient
        ing = _ingredient_par_nom(plat.nom)
        if ing:
            facteur = ing.facteur_conversion or Decimal('1')
            MouvementStockCuisine.objects.create(
                ingredient     = ing,
                type_mouvement = type_mvt,
                quantite       = Decimal(str(quantity)) * facteur,
                commentaire    = f"{label} — {plat.nom} x{quantity} — {reference}",
                utilisateur    = user,
            )
        return

    for ligne in lignes:
        facteur = ligne.ingredient.facteur_conversion or Decimal('1')
        qte     = ligne.quantite * quantity * facteur
        MouvementStockCuisine.objects.create(
            ingredient     = ligne.ingredient,
            type_mouvement = type_mvt,
            quantite       = qte,
            commentaire    = f"{label} — {plat.nom} x{quantity} — {reference}",
            utilisateur    = user,
        )
