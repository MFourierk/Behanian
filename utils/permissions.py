"""
Contrôle d'accès centralisé — Complexe Hôtelier Behanian

Groupes canoniques (sans accents pour éviter les conflits d'encodage en base) :
  Manager General     → accès complet sauf suppression transactions
  Directeur General   → alias de Manager General
  Manager Cuisine     → module cuisine uniquement
  Receptionniste      → module hôtel uniquement
  Caissiere Principale→ tous les caisses (restaurant, bar, piscine, espaces, caisse centrale)
  Caissiere           → caisses TPE uniquement (restaurant, bar, piscine, espaces) – PAS caisse centrale
  Utilisateur Simple  → aucun accès interface (gardiens, serveurs, agents)
  Responsable Cave    → module Cave complet (articles, stock, inventaire, commandes, fournisseurs)
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# ── Noms canoniques des groupes ──────────────────────────────
GROUPE_MANAGER_GENERAL    = 'Manager General'
GROUPE_DIRECTEUR_GENERAL  = 'Directeur General'
GROUPE_MANAGER_CUISINE    = 'Manager Cuisine'
GROUPE_RECEPTIONNISTE     = 'Receptionniste'
GROUPE_CAISSIERE_PRINCIPALE = 'Caissiere Principale'
GROUPE_CAISSIERE          = 'Caissiere'
GROUPE_UTILISATEUR_SIMPLE = 'Utilisateur Simple'
GROUPE_RESPONSABLE_CAVE   = 'Responsable Cave'

# Noms alternatifs (anciens groupes en base + rétrocompatibilité complète)
_MANAGERS = [
    GROUPE_MANAGER_GENERAL, GROUPE_DIRECTEUR_GENERAL,
    # Variantes accentuées / anciens formats
    'Manager Général(e)', 'Manager General(e)',
    'Directeur Général',   # nom existant en base avec accent
]
_CAISSIERE_PRINCIPALE = [
    GROUPE_CAISSIERE_PRINCIPALE,
    # Variantes anciens formats
    'Caissier(ère) Principal(e)', 'Caissier(ere) Principal(e)',
    # Chef caissier(e) : accès complet (restaurant+bar+piscine+espaces+caisse)
    # mais bloqué de la gestion bar (Cave TPE uniquement) via _is_caissier()
    'Chef caissier(e)',
]
_CAISSIERE = [
    GROUPE_CAISSIERE,
    # Variantes anciennes et nom réel trouvé en base
    'Caissier(e)',          # nom réel en base
    'Caissière / Caissier', 'Caissiere / Caissier',
    'Caissier(E)',
]
# Groupes bloqués de la gestion/stock/rapports bar (TPE bar uniquement)
_BAR_TPE_SEULEMENT = _CAISSIERE + ['Chef caissier(e)']
_RECEPTIONNISTE = [
    GROUPE_RECEPTIONNISTE,
    'Réceptionniste',       # nom réel en base avec accent
]

# Responsable Hôtel : module hôtel + gestion des chambres dans paramètres
_RESPONSABLE_HOTEL = [
    'Responsable Hôtel',
]

# Responsable Cave : module Cave complet (stock, articles, inventaire, commandes, fournisseurs)
_RESPONSABLE_CAVE = [
    GROUPE_RESPONSABLE_CAVE,
]
_UTILISATEUR_SIMPLE = [
    GROUPE_UTILISATEUR_SIMPLE,
    'Serveuse/Serveur',
    'Agent de Sécurité',   # nom réel en base — aucun accès interface
    'Cuisinier(e)',         # personnel cuisine — pas d'accès interface
]


# ── Matrice d'accès (groupe → modules) ───────────────────────
_RULES = [
    (_MANAGERS,              ['*']),
    (['Manager Cuisine'],     ['cuisine']),
    (_RECEPTIONNISTE,         ['hotel']),
    (_RESPONSABLE_HOTEL,      ['hotel', 'parametres']),
    # Responsable Cave : accès complet au module Cave (stock, articles, inventaire, commandes, fournisseurs)
    (_RESPONSABLE_CAVE,       ['bar']),
    # Caissière Principale : tout (restaurant, bar, piscine, espaces + caisse centrale)
    (_CAISSIERE_PRINCIPALE,   ['restaurant', 'bar', 'piscine', 'espaces', 'caisse']),
    # Caissière : TPE uniquement, PAS de caisse centrale
    (_CAISSIERE,              ['restaurant', 'bar', 'piscine', 'espaces']),
    # Utilisateur Simple + personnel terrain : aucun module
    (_UTILISATEUR_SIMPLE,     []),
]

ACCESS_MAP = {}
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


def _is_manager(user):
    """Vérifie si l'utilisateur est Manager Général ou Directeur Général."""
    if user.is_superuser:
        return True
    return any(g in _MANAGERS for g in get_user_groups(user))


def require_manager(view_func):
    """Décorateur — réservé au Manager Général, Directeur Général et superuser."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _is_manager(request.user):
            messages.error(request,
                "Accès refusé — réservé aux managers et directeurs.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_superuser(view_func):
    """Décorateur — réservé au superuser uniquement (suppression de transactions)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request,
                "Action réservée au Super Administrateur — la suppression de transactions est protégée.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_accessible_modules(user):
    """Retourne la liste des modules accessibles pour la sidebar."""
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
    """True pour tous les groupes limités au TPE bar (bloque gestion/stock/rapports cave)."""
    g = get_user_groups(user)
    return any(x in g for x in _BAR_TPE_SEULEMENT)

def _is_caissier_principal(user):
    g = get_user_groups(user)
    return any(x in g for x in _CAISSIERE_PRINCIPALE)

def _is_receptionniste(user):
    g = get_user_groups(user)
    return any(x in g for x in _RECEPTIONNISTE)

def _is_responsable_hotel(user):
    g = get_user_groups(user)
    return any(x in g for x in _RESPONSABLE_HOTEL)

def _is_manager_cuisine(user):
    g = get_user_groups(user)
    return 'Manager Cuisine' in g

def _is_manager_general(user):
    return _is_manager(user)


def require_chambre_access(view_func):
    """Autorise managers ET Responsable Hôtel sur les vues chambres du module paramètres."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if _is_manager(request.user) or _is_responsable_hotel(request.user) or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Accès refusé — réservé aux managers et au Responsable Hôtel.")
        return redirect('dashboard:index')
    return wrapper


def require_gestion_access(module):
    """Bloque les caissiers et réceptionnistes des pages de gestion/admin."""
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
            if _is_caissier(user):
                messages.error(request, "Accès refusé — section réservée à la gestion.")
                return redirect(fallback.get(module, 'dashboard:index'))
            if _is_receptionniste(user) and module != 'hotel':
                messages.error(request, "Accès refusé.")
                return redirect('hotel:index')
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
