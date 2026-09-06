"""
Middleware caisse — exige une CaisseSession ouverte pour toute caissière.
Les managers et superusers sont exemptés.
"""
from django.shortcuts import redirect
from django.utils import timezone


# URLs exemptées — toujours accessibles même sans session ouverte
_SESSION_EXEMPT_PREFIXES = [
    '/users/',                       # login / logout / profil
    '/static/',
    '/media/',
    '/admin/',
    '/caisse/ouvrir-session/',       # page dédiée ouverture session (toutes caissières)
    '/caisse/ouvrir/',               # endpoint AJAX caisse centrale
    '/caisse/api/cloture-oubliee/',  # clôture session oubliée (caisse principale)
    '/caisse/',                      # index caisse (Caissière Principale)
    '/dashboard/',
]


class CaisseOuverteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and not user.is_superuser:
            from utils.permissions import _is_manager, _is_caissiere_any, user_has_access
            from caisse.models import CaisseSession

            if not _is_manager(user) and _is_caissiere_any(user):
                path = request.path
                if not any(path.startswith(p) for p in _SESSION_EXEMPT_PREFIXES):
                    today = timezone.localdate()
                    has_active = CaisseSession.objects.filter(
                        user=user, is_open=True, date_session=today
                    ).exists()
                    if not has_active:
                        # Caissière Principale / Chef → caisse index (overlay attente_session)
                        if user_has_access(user, 'caisse'):
                            return redirect('/caisse/')
                        # Caissière TPE → page dédiée ouverture session
                        return redirect('/caisse/ouvrir-session/')

        return self.get_response(request)
