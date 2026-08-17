from django.db import transaction
from .models import FicheTechnique, MouvementStockCuisine, Ingredient


def _ingredient_par_nom(nom_plat):
    """Retourne le premier ingrédient actif dont le nom correspond (insensible à la casse)."""
    return Ingredient.objects.filter(nom__iexact=nom_plat, statut=True).first()


def check_stock_availability(plat, quantity=1):
    """
    Vérifie si le stock est suffisant pour préparer un plat (x portions).
    Retourne (bool, message_erreur).

    Cas couverts :
    - FT avec lignes       → vérification normale par ingrédient
    - FT sans lignes       → repli par correspondance de nom sur cuisine_ingredient
    - Pas de FT            → non bloqué (is_simple ou plat bar)
    """
    nom_plat = getattr(plat, 'nom', 'ce plat')

    if not hasattr(plat, 'fiche_technique') or plat.fiche_technique is None:
        return True, ""

    fiche = plat.fiche_technique
    lignes = list(fiche.lignes.select_related('ingredient').all())

    # FT vide → repli sur l'ingrédient homonyme
    if not lignes:
        ing = _ingredient_par_nom(nom_plat)
        if ing and ing.quantite_stock < quantity:
            return False, (
                f"« {nom_plat} » ne peut pas être servi — stock insuffisant :\n"
                f"  • {ing.nom} : {ing.quantite_stock:.0f} disponible / {quantity} nécessaire"
            )
        return True, ""

    manquants = []
    for ligne in lignes:
        qte_necessaire = ligne.quantite * quantity
        stock_dispo    = ligne.ingredient.quantite_stock
        if stock_dispo < qte_necessaire:
            manquants.append({
                'ingredient': ligne.ingredient,
                'necessaire': qte_necessaire,
                'disponible': stock_dispo,
            })

    if manquants:
        detail = "\n".join(
            f"  • {m['ingredient'].nom} : "
            f"{int(m['disponible']) if m['disponible'] == int(m['disponible']) else float(m['disponible']):.2f} disponible"
            f" / {int(m['necessaire']) if m['necessaire'] == int(m['necessaire']) else float(m['necessaire']):.2f} nécessaire"
            for m in manquants
        )
        return False, f"« {nom_plat} » ne peut pas être servi — stock insuffisant :\n{detail}"

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
            MouvementStockCuisine.objects.create(
                ingredient     = ing,
                type_mouvement = type_mvt,
                quantite       = quantity,
                commentaire    = f"{label} — {plat.nom} x{quantity} — {reference}",
                utilisateur    = user,
            )
        return

    for ligne in lignes:
        qte = ligne.quantite * quantity
        MouvementStockCuisine.objects.create(
            ingredient     = ligne.ingredient,
            type_mouvement = type_mvt,
            quantite       = qte,
            commentaire    = f"{label} — {plat.nom} x{quantity} — {reference}",
            utilisateur    = user,
        )
