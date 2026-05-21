"""
Middleware de sécurité — neutralise is_staff, contrôle d'accès par groupe
"""
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


# Page d'accueil par groupe
HOME_BY_GROUP = {
    # Managers / Direction
    'Manager General':             'dashboard:index',
    'Directeur General':           'dashboard:index',
    'Manager Général(e)':          'dashboard:index',
    'Manager General(e)':          'dashboard:index',
    'Directeur Général':           'dashboard:index',
    # Spécialistes
    'Manager Cuisine':             'cuisine:index',
    'Receptionniste':              'hotel:index',
    'Réceptionniste':              'hotel:index',
    'Responsable Hôtel':           'hotel:index',
    # Caisse Principale
    'Caissiere Principale':        'caisse:index',
    'Caissier(ère) Principal(e)':  'caisse:index',
    'Caissier(ere) Principal(e)':  'caisse:index',
    # Chef caissier(e) → module caisse centrale
    'Chef caissier(e)':            'caisse:index',
    # Caissière TPE
    'Caissiere':                   'bar:tpe',
    'Caissier(e)':                 'bar:tpe',
    'Caissier(E)':                 'bar:tpe',
    'Caissière / Caissier':        'bar:tpe',
    'Caissiere / Caissier':        'bar:tpe',
    # Sans accès interface
    'Utilisateur Simple':          'dashboard:index',
    'Serveuse/Serveur':            'dashboard:index',
    'Agent de Sécurité':           'dashboard:index',
    'Cuisinier(e)':                'dashboard:index',
}

# Chemins URL autorisés par groupe (None = tout autorisé)
_TPE = ['/bar/', '/restaurant/', '/piscine/', '/espaces-evenementiels/', '/facturation/']
_CAISSE_PLUS_TPE = ['/caisse/'] + _TPE

ALLOWED_PATHS = {
    # Managers — tout
    'Manager General':             None,
    'Directeur General':           None,
    'Manager Général(e)':          None,
    'Manager General(e)':          None,
    'Directeur Général':           None,
    # Cuisine
    'Manager Cuisine':             ['/cuisine/'],
    # Hôtel
    'Receptionniste':              ['/hotel/'],
    'Réceptionniste':              ['/hotel/'],
    'Responsable Hôtel':           ['/hotel/'],
    # Caissière Principale — caisse centrale + TPE
    'Caissiere Principale':        _CAISSE_PLUS_TPE,
    'Caissier(ère) Principal(e)':  _CAISSE_PLUS_TPE,
    'Caissier(ere) Principal(e)':  _CAISSE_PLUS_TPE,
    # Chef caissier(e) — caisse centrale + tous TPE (bar géré par require_bar_gestion)
    'Chef caissier(e)':            _CAISSE_PLUS_TPE,
    # Caissière — TPE uniquement (PAS /caisse/)
    'Caissiere':                   _TPE,
    'Caissier(e)':                 _TPE,
    'Caissier(E)':                 _TPE,
    'Caissière / Caissier':        _TPE,
    'Caissiere / Caissier':        _TPE,
    # Sans accès interface
    'Utilisateur Simple':          [],
    'Serveuse/Serveur':            [],
    'Agent de Sécurité':           [],
    'Cuisinier(e)':                [],
}

# Chemins toujours accessibles (authentifié)
ALWAYS_ALLOWED = ['/users/', '/static/', '/media/', '/dashboard/']


class StrictGroupAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and not user.is_superuser:
            # Neutraliser is_staff (aucun accès supplémentaire)
            if user.is_staff:
                user.is_staff = False

            # Bloquer /admin/ pour les non-superusers
            if request.path.startswith('/admin/'):
                return redirect('dashboard:index')

            # Vérifier que le chemin est autorisé pour le groupe
            groups = list(user.groups.values_list('name', flat=True))
            if groups:
                for group in groups:
                    allowed = ALLOWED_PATHS.get(group)
                    if allowed is None:
                        break  # Manager — tout autorisé

                    path = request.path
                    # Chemins communs toujours accessibles
                    if any(path.startswith(a) for a in ALWAYS_ALLOWED):
                        break

                    # Vérifier si le chemin est dans les paths autorisés
                    if not any(path.startswith(a) for a in allowed):
                        home = HOME_BY_GROUP.get(group, 'dashboard:index')
                        try:
                            return redirect(home)
                        except NoReverseMatch:
                            return redirect('dashboard:index')

        return self.get_response(request)
