"""
Context processor — injecte les modules accessibles et infos de rôle dans tous les templates
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
        # Noms canoniques
        'Manager General':            'Manager Général',
        'Directeur General':          'Directeur Général',
        'Manager Cuisine':            'Manager Cuisine',
        'Receptionniste':             'Réceptionniste',
        'Caissiere Principale':       'Caissière Principale',
        'Caissiere':                  'Caissière',
        'Utilisateur Simple':         'Utilisateur',
        # Noms réels trouvés en base
        'Manager Général(e)':         'Manager Général',
        'Manager General(e)':         'Manager Général',
        'Directeur Général':          'Directeur Général',
        'Réceptionniste':             'Réceptionniste',
        'Responsable Hôtel':          'Responsable Hôtel',
        'Caissier(e)':                'Caissier(ère)',
        'Caissier(E)':                'Caissier(ère)',
        'Caissière / Caissier':       'Caissier(ère)',
        'Caissiere / Caissier':       'Caissier(ère)',
        'Caissier(ère) Principal(e)': 'Caissier Principal',
        'Caissier(ere) Principal(e)': 'Caissier Principal',
        'Responsable Caisse':         'Responsable Caisse',
        'Serveuse/Serveur':           'Serveur',
        'Agent de Sécurité':          'Agent de Sécurité',
        'Cuisinier(e)':               'Cuisinier(ère)',
    }
    role = 'Administrateur'
    if request.user.is_superuser:
        role = 'Super Admin'
    elif groups:
        role = role_map.get(groups[0], groups[0])

    # Page d'accueil selon le groupe
    home_map = {
        # Noms canoniques
        'Manager General':            'dashboard:index',
        'Directeur General':          'dashboard:index',
        'Manager Cuisine':            'cuisine:index',
        'Receptionniste':             'hotel:index',
        'Caissiere Principale':       'caisse:index',
        'Caissiere':                  'bar:tpe',
        'Utilisateur Simple':         'dashboard:index',
        # Noms réels en base
        'Manager Général(e)':         'dashboard:index',
        'Manager General(e)':         'dashboard:index',
        'Directeur Général':          'dashboard:index',
        'Réceptionniste':             'hotel:index',
        'Responsable Hôtel':          'hotel:index',
        'Caissier(e)':                'bar:tpe',
        'Caissier(E)':                'bar:tpe',
        'Caissière / Caissier':       'bar:tpe',
        'Caissiere / Caissier':       'bar:tpe',
        'Caissier(ère) Principal(e)': 'caisse:index',
        'Caissier(ere) Principal(e)': 'caisse:index',
        'Responsable Caisse':         'bar:tpe',
        'Serveuse/Serveur':           'dashboard:index',
        'Agent de Sécurité':          'dashboard:index',
        'Cuisinier(e)':               'dashboard:index',
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
