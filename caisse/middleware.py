"""
Middleware caisse — seule la caisse CENTRALE a un cycle ouverture/clôture journalier.
Les modules (restaurant, bar, piscine, espaces) n'ont plus de session propre :
ils peuvent enregistrer des transactions à tout moment.
"""
from django.utils.deprecation import MiddlewareMixin


class CaisseOuverteMiddleware(MiddlewareMixin):
    """
    Plus de blocage par module.
    L'ouverture/clôture concerne uniquement la caisse centrale (/caisse/).
    """

    def process_request(self, request):
        # Aucun blocage — chaque module opère librement
        return None
