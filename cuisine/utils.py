from django.db import transaction
from .models import FicheTechnique, MouvementStock

def check_stock_availability(plat, quantity=1):
    """
    Vérifie si le stock est suffisant pour un plat donné (et une quantité).
    Uniquement basé sur la fiche technique.
    Retourne (bool, message_erreur).
    """
    if hasattr(plat, 'fiche_technique'):
        possible, manquants = plat.fiche_technique.check_stock(quantity)
        if not possible:
            # La clé est 'article' comme défini dans FicheTechnique.check_stock
            details = ", ".join([f"{m['article'].nom} (Manque {m['manque']})" for m in manquants])
            return False, f"Articles manquants : {details}"
        return True, ""

    # Si pas de fiche technique, on considère que c'est possible (produit direct, service, etc.)
    return True, ""

def process_stock_movement(plat, quantity, movement_type, user, reference):
    """
    Effectue les mouvements de stock pour un plat basé sur sa fiche technique.
    movement_type: 'sortie' (vente) ou 'entree' (annulation)
    """
    if hasattr(plat, 'fiche_technique'):
        if movement_type == 'sortie':
            plat.fiche_technique.deduire_stock(quantity, user)
        elif movement_type == 'entree':
            # La méthode restaurer_stock crée un mouvement d'inventaire, 
            # ce qui est sémantiquement plus correct pour une annulation.
            plat.fiche_technique.restaurer_stock(quantity, user)
