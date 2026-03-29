from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import CaisseSession


MODULES_PROTEGES = [
    '/restaurant/api/',
    '/bar/api/',
    '/piscine/api/',
    '/hotel/api/',
    '/espaces-evenementiels/api/',
]


class CaisseOuverteMiddleware(MiddlewareMixin):
    """
    Bloque les transactions (POST API) si aucune caisse n'est ouverte.
    Ne bloque pas les lectures (GET) ni les pages de configuration.
    """

    def process_request(self, request):
        if request.method != 'POST':
            return None

        path = request.path
        if not any(path.startswith(p) for p in MODULES_PROTEGES):
            return None

        # Exclure les URLs qui ne créent pas de tickets
        exclusions = ['login', 'logout', 'static', 'media', 'admin', 'caisse']
        if any(e in path for e in exclusions):
            return None

        # Vérifier si une caisse est ouverte
        if not CaisseSession.objects.filter(is_open=True).exists():
            return JsonResponse({
                'success': False,
                'error': '⚠️ Caisse non ouverte. Veuillez ouvrir la caisse avant d\'enregistrer des transactions.',
                'caisse_fermee': True,
            }, status=403)

        return None
