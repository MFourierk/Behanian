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
GROUPE_CAISSIER_PRINCIPAL = 'Responsable Caisse'
GROUPE_SERVEUR            = 'Serveuse/Serveur'

# Modules accessibles par groupe
# Tous les noms de groupes possibles (avec/sans accents)
ACCESS_MAP = {}
_RULES = [
    (['Manager Général(e)', 'Manager General(e)'],        ['*']),
    (['Manager Cuisine'],                                  ['cuisine']),
    (['Réceptionniste', 'Receptionniste'],                 ['hotel']),
    (['Caissière / Caissier', 'Caissiere / Caissier'],    ['restaurant', 'bar', 'piscine', 'espaces']),
    (['Caissier(ère) Principal(e)', 'Caissier(ere) Principal(e)'], ['caisse']),
    (['Serveuse/Serveur'],                                 []),
]
for _names, _modules in _RULES:
    for _n in _names:
        ACCESS_MAP[_n] = _modules


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


# ── Décorateurs de restriction intra-module ──────────────────

def _is_caissier(user):
    g = get_user_groups(user)
    return any(x in g for x in ['Caissière / Caissier','Caissiere / Caissier'])

def _is_receptionniste(user):
    g = get_user_groups(user)
    return 'Réceptionniste' in g or 'Receptionniste' in g

def _is_manager_cuisine(user):
    g = get_user_groups(user)
    return 'Manager Cuisine' in g

def _is_manager_general(user):
    g = get_user_groups(user)
    return user.is_superuser or 'Manager Général(e)' in g or 'Manager General(e)' in g


def require_gestion_access(module):
    """Bloque les caissiers et réceptionnistes des pages de gestion/admin."""
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    # URLs de repli par module
    fallback = {
        'bar':        'bar:tpe',
        'restaurant': 'restaurant:index',
        'hotel':      'hotel:index',
        'cuisine':    'cuisine:index',
        'piscine':    'piscine:index',
        'caisse':     'caisse:index',
        'facturation':'facturation:index',
    }

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            # Caissiers — accès TPE uniquement
            if _is_caissier(user):
                messages.error(request, "Accès refusé — section réservée à la gestion.")
                return redirect(fallback.get(module, 'dashboard:index'))
            # Réceptionnistes — hotel uniquement, pas d'admin structurel
            if _is_receptionniste(user) and module != 'hotel':
                messages.error(request, "Accès refusé.")
                return redirect('hotel:index')
            # Manager Cuisine — cuisine uniquement
            if _is_manager_cuisine(user) and module not in ['cuisine']:
                messages.error(request, "Accès refusé.")
                return redirect('cuisine:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def caisse_est_ouverte(user):
    """Vérifie si une caisse est ouverte pour cet utilisateur ou toute caisse du jour."""
    from caisse.models import CaisseSession
    return CaisseSession.objects.filter(is_open=True).exists()


def verifier_caisse_ouverte(request):
    """Retourne True si une caisse est ouverte, sinon False."""
    from caisse.models import CaisseSession
    return CaisseSession.objects.filter(is_open=True).exists()
