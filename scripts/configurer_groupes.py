"""
Script de configuration des groupes et permissions — Complexe Hôtelier Behanian
Exécuter avec : python manage.py shell < scripts/configurer_groupes.py
ou             : python manage.py runscript configurer_groupes
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def get_perms(app, codenames):
    """Récupère les permissions par app et codename."""
    perms = []
    for c in codenames:
        try:
            p = Permission.objects.get(content_type__app_label=app, codename=c)
            perms.append(p)
        except Permission.DoesNotExist:
            print(f"  ⚠️  Permission introuvable : {app}.{c}")
    return perms

def get_all_perms(app, exclude_actions=None):
    """Récupère toutes les permissions d'une app en excluant certaines actions."""
    exclude_actions = exclude_actions or []
    return list(Permission.objects.filter(
        content_type__app_label=app
    ).exclude(
        codename__startswith=tuple(f'{a}_' for a in exclude_actions) if exclude_actions else ('__never__',)
    ))

def configurer_groupe(nom, permissions_list, description=""):
    group, created = Group.objects.get_or_create(name=nom)
    group.permissions.clear()
    for perm in permissions_list:
        group.permissions.add(perm)
    action = "Créé" if created else "Mis à jour"
    print(f"\n✅ {action} : {nom} — {group.permissions.count()} permissions")
    return group


print("=" * 60)
print("Configuration des groupes — Behanian")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# 1. MANAGER GÉNÉRAL
# Accès complet à TOUT sauf : delete sur tickets/factures/avoirs/historiques
# ══════════════════════════════════════════════════════════════
INTOUCHABLES = [
    # Facturation — pas de suppression
    'delete_ticket', 'delete_facture', 'delete_avoir', 'delete_ligneavoir',
    'delete_lignefacture', 'delete_proforma', 'delete_ligneproforma',
    # Caisse — pas de suppression session
    'delete_caissesession',
    # Mouvements de stock — pas de suppression (traçabilité)
    'delete_mouvementstock', 'delete_mouvementstockcuisine',
    'delete_mouvementstockbar',
    # Historique Django admin
    'delete_logentry',
]

manager_general_perms = []
for app in ['bar', 'restaurant', 'hotel', 'cuisine', 'piscine', 'boite_nuit',
            'espaces_evenementiels', 'caisse', 'facturation', 'parametres']:
    for p in Permission.objects.filter(content_type__app_label=app):
        if p.codename not in INTOUCHABLES:
            manager_general_perms.append(p)

# Auth — voir et gérer les utilisateurs mais pas supprimer les permissions système
for p in Permission.objects.filter(content_type__app_label='auth'):
    if p.codename not in ['delete_permission', 'delete_group']:
        manager_general_perms.append(p)

configurer_groupe('Manager Général(e)', manager_general_perms,
    "Accès complet sauf suppression des traces financières")


# ══════════════════════════════════════════════════════════════
# 2. MANAGER CUISINE
# Tout ce qui concerne la cuisine uniquement
# Pas de suppression des bons de réception ni des mouvements de stock
# ══════════════════════════════════════════════════════════════
cuisine_perms = []

# Cuisine complète sauf delete sur réceptions et mouvements
for p in Permission.objects.filter(content_type__app_label='cuisine'):
    if p.codename not in [
        'delete_bonreception', 'delete_bonreceptioncuisine',
        'delete_lignebonreception', 'delete_lignebonreceptioncuisine',
        'delete_mouvementstock', 'delete_mouvementstockcuisine',
    ]:
        cuisine_perms.append(p)

# Voir les plats du restaurant (pour coordination)
cuisine_perms += get_perms('restaurant', ['view_platmenu', 'view_categoriemenu'])

# Voir facturation (tickets liés cuisine) mais pas modifier
cuisine_perms += get_perms('facturation', ['view_ticket', 'view_facture'])

configurer_groupe('Manager Cuisine', cuisine_perms,
    "Cuisine complète — pas de suppression des bons de réception ni mouvements")


# ══════════════════════════════════════════════════════════════
# 3. RÉCEPTIONNISTE
# Module Hôtel uniquement — opérations courantes
# Pas de suppression de chambres, ni de manipulation administrative
# ══════════════════════════════════════════════════════════════
receptionniste_perms = []

# Hôtel — tout sauf suppression des chambres et clients
for p in Permission.objects.filter(content_type__app_label='hotel'):
    if p.codename not in ['delete_chambre', 'delete_client']:
        receptionniste_perms.append(p)

# Facturation — créer et voir les tickets hôtel, pas supprimer
receptionniste_perms += get_perms('facturation', [
    'add_ticket', 'change_ticket', 'view_ticket',
    'add_client', 'change_client', 'view_client',
    'view_facture',
])

# Voir boissons et plats pour les commandes en chambre
receptionniste_perms += get_perms('bar', ['view_boissonbar', 'view_categoriebar'])
receptionniste_perms += get_perms('restaurant', ['view_platmenu', 'view_categoriemenu'])
receptionniste_perms += get_perms('espaces_evenementiels', ['view_espaceevenementiel'])

# Voir les utilisateurs (pour sélection serveur sur tickets)
receptionniste_perms += get_perms('auth', ['view_user', 'view_group'])

configurer_groupe('Réceptionniste', receptionniste_perms,
    "Module Hôtel uniquement — check-in/out/commandes chambre")


# ══════════════════════════════════════════════════════════════
# 4. CAISSIER / CAISSIÈRE
# Restaurant, Cave (Bar), Piscine — facturation uniquement
# Pas d'accès administratif ni structurel
# ══════════════════════════════════════════════════════════════
caissier_perms = []

# Restaurant — commandes et facturation (pas gestion des plats/tables)
caissier_perms += get_perms('restaurant', [
    'add_commande', 'change_commande', 'view_commande',
    'add_lignecommande', 'change_lignecommande', 'view_lignecommande',
    'view_table', 'view_platmenu', 'view_categoriemenu',
])

# Bar/Cave — ventes et stock (pas gestion catalogue)
caissier_perms += get_perms('bar', [
    'view_boissonbar', 'view_categoriebar', 'view_tablebar',
    'add_mouvementstockbar', 'view_mouvementstockbar',
])

# Piscine — accès et facturation
for p in Permission.objects.filter(content_type__app_label='piscine'):
    if 'delete' not in p.codename:
        caissier_perms.append(p)

# Facturation — créer tickets et voir, pas supprimer
caissier_perms += get_perms('facturation', [
    'add_ticket', 'change_ticket', 'view_ticket',
    'view_facture', 'add_client', 'view_client',
])

# Caisse — ouvrir/fermer session
caissier_perms += get_perms('caisse', [
    'add_caissesession', 'change_caissesession', 'view_caissesession',
])

# Voir les utilisateurs pour sélection serveur
caissier_perms += get_perms('auth', ['view_user', 'view_group'])

configurer_groupe('Caissière / Caissier', caissier_perms,
    "Restaurant, Cave, Piscine — facturation uniquement")


# ══════════════════════════════════════════════════════════════
# 5. SERVEUSE / SERVEUR
# Aucun accès système — uniquement présents pour apparaître
# dans les listes de sélection sur les tickets et factures
# ══════════════════════════════════════════════════════════════
configurer_groupe('Serveuse/Serveur', [],
    "Aucune permission — présence pour sélection dans tickets")


# ══════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("RÉSUMÉ FINAL")
print("=" * 60)
for g in Group.objects.all().order_by('name'):
    users = g.user_set.all()
    print(f"\n📋 {g.name}")
    print(f"   Permissions : {g.permissions.count()}")
    print(f"   Utilisateurs : {', '.join(u.username for u in users) if users else 'aucun'}")

print("\n✅ Configuration terminée")
print("=" * 60)
