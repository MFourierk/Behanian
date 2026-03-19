"""
Context processor — injecte les modules accessibles dans tous les templates
"""
from utils.permissions import get_accessible_modules, get_user_groups


def user_permissions_context(request):
    """Injecte les infos de permission dans chaque template."""
    if not request.user.is_authenticated:
        return {}

    modules = get_accessible_modules(request.user)
    groups  = get_user_groups(request.user)

    # Rôle principal affiché dans la sidebar
    role_map = {
        'Manager Général(e)':   'Manager Général',
        'Manager Cuisine':      'Manager Cuisine',
        'Réceptionniste':       'Réceptionniste',
        'Caissière / Caissier': 'Caissier(ère)',
        'Serveuse/Serveur':     'Serveur / Serveuse',
    }
    role = 'Administrateur'
    if request.user.is_superuser:
        role = 'Super Admin'
    elif groups:
        role = role_map.get(groups[0], groups[0])

    # Page d'accueil selon le groupe
    home_map = {
        'Manager Général(e)':      'dashboard:index',
        'Manager General(e)':      'dashboard:index',
        'Manager Cuisine':         'cuisine:index',
        'Réceptionniste':          'hotel:index',
        'Receptionniste':          'hotel:index',
        'Caissière / Caissier':    'bar:tpe',
        'Caissiere / Caissier':    'bar:tpe',
        'Caissier(ère) Principal(e)': 'caisse:index',
        'Caissier(ere) Principal(e)': 'caisse:index',
    }
    home_url = 'dashboard:index'
    for g in groups:
        if g in home_map:
            home_url = home_map[g]
            break

    return {
        'accessible_modules': modules,
        'user_role':          role,
        'user_groups':        groups,
        'user_home_url':      home_url,
    }
