"""
Contrôle d'accès centralisé — Complexe Hôtelier Behanian
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# ── Définition des groupes ──────────────────────────────────
GROUPE_MANAGER_GENERAL  = 'Manager Général(e)'
GROUPE_MANAGER_CUISINE  = 'Manager Cuisine'
GROUPE_RECEPTIONNISTE   = 'Réceptionniste'
GROUPE_CAISSIER         = 'Caissière / Caissier'
GROUPE_SERVEUR          = 'Serveuse/Serveur'

# Modules accessibles par groupe
ACCESS_MAP = {
    GROUPE_MANAGER_GENERAL: ['*'],
    GROUPE_MANAGER_CUISINE: ['cuisine'],
    GROUPE_RECEPTIONNISTE:  ['hotel'],
    GROUPE_CAISSIER:        ['restaurant', 'bar', 'piscine', 'espaces', 'caisse'],
    GROUPE_SERVEUR:         [],
}

# Modules nécessitant le superuser ou Manager Général uniquement
ADMIN_ONLY_MODULES = ['parametres']
MANAGER_ONLY_MODULES = ['facturation', 'caisse']

def get_user_groups(user):
    """Retourne les noms de groupes de l'utilisateur."""
    return list(user.groups.values_list('name', flat=True))

def user_has_access(user, module):
    """Vérifie si l'utilisateur peut accéder à un module."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    groups = get_user_groups(user)
    for g in groups:
        allowed = ACCESS_MAP.get(g, [])
        if '*' in allowed or module in allowed:
            return True
    return False

def user_can_delete_transactions(user):
    """Seul le superuser peut supprimer des transactions."""
    return user.is_superuser

def require_module_access(module):
    """Décorateur — refuse l'accès si le module n'est pas autorisé."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not user_has_access(request.user, module):
                messages.error(request,
                    f"Accès refusé — vous n'avez pas les droits pour accéder à ce module.")
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_accessible_modules(user):
    """Retourne la liste des modules accessibles pour affichage sidebar."""
    if user.is_superuser:
        return ['dashboard', 'hotel', 'restaurant', 'bar', 'cuisine',
                'piscine', 'boite_nuit', 'espaces', 'caisse', 'facturation',
                'parametres', 'users']
    groups = get_user_groups(user)
    modules = set()
    modules.add('dashboard')  # Dashboard toujours visible
    for g in groups:
        allowed = ACCESS_MAP.get(g, [])
        if '*' in allowed:
            modules.update(['hotel', 'restaurant', 'bar', 'cuisine',
                           'piscine', 'boite_nuit', 'espaces', 'caisse',
                           'facturation', 'parametres'])
        else:
            modules.update(allowed)
    return list(modules)
