from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import CaisseSession


# URLs protégées par module → type de session requis
MODULES_PROTEGES = {
    '/restaurant/api/': 'module',
    '/bar/api/':        'module',
    '/piscine/api/':    'module',
    '/espaces-evenementiels/api/': 'module',
    '/hotel/api/':      'hotel',
    '/hotel/checkout':  'hotel',
}

# URLs à exclure même dans les modules protégés
EXCLUSIONS = [
    'login', 'logout', 'static', 'media', 'admin',
    'get_', 'list', 'detail', 'check', 'status',
]


class CaisseOuverteMiddleware(MiddlewareMixin):
    """
    Vérifie qu'une caisse est ouverte avant toute transaction.
    
    Logique :
    - Hôtel       → session ouverte par un Réceptionniste ou Manager
    - Autres modules → session ouverte par un Caissier(e) ou Manager
    - La caisse centrale (Manager) peut toujours opérer
    """

    def process_request(self, request):
        if request.method != 'POST':
            return None

        path = request.path
        module_type = None
        for prefix, mtype in MODULES_PROTEGES.items():
            if path.startswith(prefix):
                module_type = mtype
                break

        if not module_type:
            return None

        # Exclure les actions de lecture
        if any(e in path for e in EXCLUSIONS):
            return None

        # Superuser et Manager peuvent toujours opérer
        if request.user.is_superuser:
            return None

        user_groups = list(request.user.groups.values_list('name', flat=True))
        manager_groups = ['Manager Général(e)', 'Directeur Général', 'Responsable Caisse', 'Responsable Hôtel']
        if any(g in user_groups for g in manager_groups):
            return None

        # Vérifier session caisse selon le type de module
        if module_type == 'hotel':
            # Hôtel : session ouverte par cet utilisateur ou un réceptionniste
            session_ouverte = CaisseSession.objects.filter(
                is_open=True,
                type_caisse='hotel'
            ).exists()
        else:
            # Autres modules : session caisse module ouverte
            session_ouverte = CaisseSession.objects.filter(
                is_open=True,
                type_caisse='module'
            ).exists()

        if not session_ouverte:
            return JsonResponse({
                'success': False,
                'ok': False,
                'error': '⚠️ Caisse non ouverte. Veuillez ouvrir la caisse avant d\'enregistrer des transactions.',
                'caisse_fermee': True,
            }, status=403)

        return None
