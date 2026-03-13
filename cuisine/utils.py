from django.db import transaction
from .models import FicheTechnique, MouvementStockCuisine


def check_stock_availability(plat, quantity=1):
    """
    Vérifie si le stock est suffisant pour préparer un plat (x portions).
    Retourne (bool, message_erreur).
    """
    if not hasattr(plat, 'fiche_technique') or plat.fiche_technique is None:
        # Pas de fiche technique → on ne bloque pas
        return True, ""

    fiche = plat.fiche_technique
    manquants = []

    for ligne in fiche.lignes.select_related('ingredient').all():
        qte_necessaire = ligne.quantite * quantity
        stock_dispo = ligne.ingredient.quantite_stock
        if stock_dispo < qte_necessaire:
            manquants.append({
                'ingredient': ligne.ingredient,
                'necessaire': qte_necessaire,
                'disponible': stock_dispo,
                'manque':     qte_necessaire - stock_dispo,
            })

    if manquants:
        details = ", ".join(
            f"{m['ingredient'].nom} (manque {m['manque']:.3f})"
            for m in manquants
        )
        return False, f"Ingrédients insuffisants : {details}"

    return True, ""


@transaction.atomic
def process_stock_movement(plat, quantity, movement_type, user, reference=""):
    """
    Effectue les mouvements de stock pour un plat basé sur sa fiche technique.
    movement_type : 'sortie' (vente/production) ou 'entree' (annulation)
    """
    if not hasattr(plat, 'fiche_technique') or plat.fiche_technique is None:
        return

    fiche = plat.fiche_technique
    type_mvt = 'production' if movement_type == 'sortie' else 'inventaire'

    for ligne in fiche.lignes.select_related('ingredient').all():
        qte = ligne.quantite * quantity
        MouvementStockCuisine.objects.create(
            ingredient     = ligne.ingredient,
            type_mouvement = type_mvt,
            quantite       = qte,
            commentaire    = f"{'Production' if movement_type == 'sortie' else 'Annulation'} — {plat.nom} x{quantity} — {reference}",
            utilisateur    = user,
        )