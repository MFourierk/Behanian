"""
Script de configuration des groupes et permissions — Complexe Hôtelier Behanian
Lancer : Get-Content scripts\configurer_groupes.py | python manage.py shell
"""
from django.contrib.auth.models import Group, Permission, User

def get_perms(app, codenames):
    perms = []
    for c in codenames:
        try:
            perms.append(Permission.objects.get(content_type__app_label=app, codename=c))
        except Permission.DoesNotExist:
            print(f"  ⚠️  {app}.{c} introuvable")
    return perms

def cfg(nom, perms):
    g, created = Group.objects.get_or_create(name=nom)
    g.permissions.set(perms)
    print(f"  {'✅ Créé' if created else '🔄 MàJ'} : {nom} — {g.permissions.count()} permissions")
    return g

print("="*60)
print("Configuration groupes Behanian")
print("="*60)

# ── 1. MANAGER GÉNÉRAL ─────────────────────────────────────
INTOUCHABLES = [
    'delete_ticket','delete_facture','delete_avoir','delete_ligneavoir',
    'delete_lignefacture','delete_proforma','delete_ligneproforma',
    'delete_caissesession','delete_mouvementstock',
    'delete_mouvementstockcuisine','delete_mouvementstockbar',
    'delete_logentry','delete_permission','delete_group',
]
mg_perms = []
for app in ['bar','restaurant','hotel','cuisine','piscine','boite_nuit',
            'espaces_evenementiels','caisse','facturation','parametres']:
    for p in Permission.objects.filter(content_type__app_label=app):
        if p.codename not in INTOUCHABLES:
            mg_perms.append(p)
for p in Permission.objects.filter(content_type__app_label='auth'):
    if p.codename not in INTOUCHABLES:
        mg_perms.append(p)
cfg('Manager Général(e)', mg_perms)

# ── 2. MANAGER CUISINE ─────────────────────────────────────
mc_perms = []
for p in Permission.objects.filter(content_type__app_label='cuisine'):
    if p.codename not in ['delete_bonreception','delete_bonreceptioncuisine',
                          'delete_lignebonreception','delete_lignebonreceptioncuisine',
                          'delete_mouvementstock','delete_mouvementstockcuisine']:
        mc_perms.append(p)
mc_perms += get_perms('restaurant', ['view_platmenu','view_categoriemenu'])
mc_perms += get_perms('facturation', ['view_ticket','view_facture'])
cfg('Manager Cuisine', mc_perms)

# ── 3. RÉCEPTIONNISTE ──────────────────────────────────────
rcp_perms = []
for p in Permission.objects.filter(content_type__app_label='hotel'):
    if p.codename not in ['delete_chambre','delete_client']:
        rcp_perms.append(p)
rcp_perms += get_perms('facturation', ['add_ticket','change_ticket','view_ticket','add_client','change_client','view_client','view_facture'])
rcp_perms += get_perms('bar', ['view_boissonbar','view_categoriebar'])
rcp_perms += get_perms('restaurant', ['view_platmenu','view_categoriemenu'])
rcp_perms += get_perms('espaces_evenementiels', ['view_espaceevenementiel'])
rcp_perms += get_perms('auth', ['view_user','view_group'])
cfg('Réceptionniste', rcp_perms)

# ── 4. CAISSIER/CAISSIÈRE (Resto, Cave, Piscine, Espaces) ──
cs_perms = []
cs_perms += get_perms('restaurant', ['add_commande','change_commande','view_commande',
    'add_lignecommande','change_lignecommande','view_lignecommande',
    'view_table','view_platmenu','view_categoriemenu'])
cs_perms += get_perms('bar', ['view_boissonbar','view_categoriebar','view_tablebar',
    'add_mouvementstockbar','view_mouvementstockbar'])
for p in Permission.objects.filter(content_type__app_label='piscine'):
    if 'delete' not in p.codename:
        cs_perms.append(p)
for p in Permission.objects.filter(content_type__app_label='espaces_evenementiels'):
    if 'delete' not in p.codename:
        cs_perms.append(p)
cs_perms += get_perms('facturation', ['add_ticket','change_ticket','view_ticket','add_client','view_client'])
cs_perms += get_perms('auth', ['view_user','view_group'])
cfg('Caissière / Caissier', cs_perms)

# ── 5. CAISSIER/CAISSIÈRE PRINCIPAL(E) — Module Caisse ─────
cp_perms = []
cp_perms += get_perms('caisse', ['add_caissesession','change_caissesession','view_caissesession'])
cp_perms += get_perms('facturation', ['view_ticket','view_facture','add_ticket','change_ticket','add_client','view_client'])
cp_perms += get_perms('auth', ['view_user','view_group'])
# Accès en lecture sur tous les modules pour les stats caisse
for app in ['hotel','restaurant','bar','piscine','espaces_evenementiels']:
    cp_perms += list(Permission.objects.filter(content_type__app_label=app, codename__startswith='view_'))
cfg('Caissier(ère) Principal(e)', cp_perms)

# ── 6. SERVEUSE/SERVEUR ────────────────────────────────────
cfg('Serveuse/Serveur', [])

# ── RETIRER is_staff de tous les utilisateurs non-superuser ─
print("\n🔐 Nettoyage is_staff...")
for u in User.objects.filter(is_superuser=False, is_staff=True):
    u.is_staff = False
    u.save()
    print(f"  {u.username} : is_staff → False")

# ── RÉSUMÉ ─────────────────────────────────────────────────
print("\n" + "="*60)
print("RÉSUMÉ")
print("="*60)
for g in Group.objects.all().order_by('name'):
    users = ', '.join(u.username for u in g.user_set.all()) or 'aucun'
    print(f"  {g.name} ({g.permissions.count()} perms) → {users}")
print("\n✅ Terminé")
