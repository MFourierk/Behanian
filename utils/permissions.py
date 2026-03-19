"""
Contrôle d'accès centralisé — Complexe Hôtelier Behanian
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# ── Définition des groupes ──
GROUPE_MANAGER_GENERAL    = 'Manager Général(e)'
GROUPE_MANAGER_CUISINE    = 'Manager Cuisine'
GROUPE_RECEPTIONNISTE     = 'Réceptionniste'
GROUPE_CAISSIER           = 'Caissière / Caissier'
GROUPE_CAISSIER_PRINCIPAL = 'Caissier(ère) Principal(e)'
GROUPE_SERVEUR            = 'Serveuse/Serveur'

# Modules accessibles par groupe
ACCESS_MAP = {
    GROUPE_MANAGER_GENERAL:    ['*'],
    GROUPE_MANAGER_CUISINE:    ['cuisine'],
    GROUPE_RECEPTIONNISTE:     ['hotel'],
    GROUPE_CAISSIER:           ['restaurant', 'bar', 'piscine', 'espaces'],
    GROUPE_CAISSIER_PRINCIPAL: ['caisse'],
    GROUPE_SERVEUR:            [],
    # Alias sans accents (compatibilite script Windows)
    'Manager General(e)':      ['*'],
    'Receptionniste':          ['hotel'],
    'Caissiere / Caissier':    ['restaurant', 'bar', 'piscine', 'espaces'],
    'Caissier(ere) Principal(e)': ['caisse'],
}


def get_user_groups(user):
    """Retourne les noms de groupes de l'utilisateur."""
    return list(user.groups.values_list('name', flat=True))


def user_has_access(user, module):
    """Vérifie si l'utilisateur peut accéder à un module."""
    if not user.is_authenticated:
        return False
    # Seul le superuser a un accès global — is_staff ne donne AUCUN accès supplémentaire
    if user.is_superuser:
        return True
    groups = get_user_groups(user)
    for g in groups:
        allowed = ACCESS_MAP.get(g, [])
        if '*' in allowed or module in allowed:
            return True
    return False


def require_module_access(module):
    """Décorateur — refuse l'accès si le module n'est pas autorisé."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not user_has_access(request.user, module):
                messages.error(request,
                    "Accès refusé — vous n'avez pas les droits pour accéder à ce module.")
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_manager(view_func):
    """Décorateur — réservé au Manager Général et superuser."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        groups = get_user_groups(request.user)
        if not request.user.is_superuser and GROUPE_MANAGER_GENERAL not in groups:
            messages.error(request, "Accès refusé — réservé au Manager Général.")
            return redirect('caisse:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_accessible_modules(user):
    """Retourne la liste des modules accessibles pour la sidebar."""
    # is_staff seul ne donne AUCUN accès module — uniquement superuser
    if user.is_superuser:
        return ['dashboard', 'hotel', 'restaurant', 'bar', 'cuisine',
                'piscine', 'boite_nuit', 'espaces', 'caisse', 'facturation',
                'parametres', 'users']
    groups = get_user_groups(user)
    modules = {'dashboard'}
    for g in groups:
        allowed = ACCESS_MAP.get(g, [])
        if '*' in allowed:
            modules.update(['hotel', 'restaurant', 'bar', 'cuisine',
                           'piscine', 'boite_nuit', 'espaces', 'caisse',
                           'facturation', 'parametres'])
        else:
            modules.update(allowed)
    return list(modules)
