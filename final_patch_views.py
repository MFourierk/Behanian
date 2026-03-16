"""
Patch final — copie la logique EXACTE de la Cave dans restaurant_tpe
"""
import os

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    contenu = f.read()

# Backup
with open(VIEWS_PATH + '.bak_final', 'w', encoding='utf-8') as f:
    f.write(contenu)
print("Backup cree")

# Trouver debut et fin de restaurant_tpe
lines = contenu.splitlines(keepends=True)
debut = None
fin = None

for i, line in enumerate(lines):
    if 'def restaurant_tpe(request):' in line:
        debut = i - 1 if i > 0 and '@login_required' in lines[i-1] else i
    if debut is not None and i > debut + 5:
        stripped = line.strip()
        if stripped.startswith('def ') or stripped.startswith('@login_required') or stripped.startswith('class '):
            fin = i
            break

if debut is None:
    print("ERREUR: restaurant_tpe introuvable")
    exit(1)
if fin is None:
    fin = len(lines)

print(f"Remplacement lignes {debut+1} a {fin}")

# Nouvelle fonction — copie exacte de la logique Cave
NOUVELLE = '''@login_required
def restaurant_tpe(request):
    """Interface TPE Restaurant — logique Cave"""
    from bar.models import BoissonBar, CategorieBar
    from django.contrib.auth.models import User, Group
    from dashboard.models import Configuration

    # Boissons Cave — EXACTEMENT comme bar_tpe
    boissons_bar = BoissonBar.objects.select_related('categorie').filter(
        statut='actif', disponible=True
    ).order_by('categorie__nom', 'nom')
    categories_bar = CategorieBar.objects.order_by('nom')

    # Plats cuisine
    from restaurant.models import CategorieMenu, PlatMenu
    mots_boisson = ['boisson', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
    categories_cuisine = [
        c for c in CategorieMenu.objects.all()
        if not any(m in c.nom.lower() for m in mots_boisson)
    ]
    ids_cuisine = [c.id for c in categories_cuisine]
    plats = PlatMenu.objects.filter(
        disponible=True, categorie__id__in=ids_cuisine
    ).select_related('categorie') if ids_cuisine else PlatMenu.objects.none()

    # Stock plats
    for plat in plats:
        plat.en_stock = True
        plat.stock_quantity = 999
        try:
            from cuisine.utils import check_stock_availability
            is_available, _ = check_stock_availability(plat, 1)
            plat.en_stock = is_available
        except:
            pass

    # Stock boissons
    for b in boissons_bar:
        b.stock_quantity = int(b.quantite_stock)

    # Serveurs — EXACTEMENT comme bar_tpe
    try:
        groupe_serveurs = Group.objects.get(name='Serveuse/Serveur')
        serveurs = User.objects.filter(
            groups=groupe_serveurs,
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
    except Group.DoesNotExist:
        serveurs = User.objects.none()

    # Tables et commandes
    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
    ).order_by('-date_modification').prefetch_related('lignes', 'table')
    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)

    config = Configuration.load()

    context = {
        'categories':        CategorieMenu.objects.all(),
        'plats':             plats,
        'categories_cuisine': categories_cuisine,
        'categories_bar':    categories_bar,
        'boissons_bar':      boissons_bar,
        'tables':            tables,
        'accompagnements':   accompagnements,
        'commandes_en_cours': commandes_en_cours_list.count(),
        'commandes_en_cours_list': commandes_en_cours_list,
        'config':            config,
        'serveurs':          serveurs,
    }
    return render(request, 'restaurant/index.html', context)

'''

nouveau_contenu = ''.join(lines[:debut]) + NOUVELLE + ''.join(lines[fin:])

with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
    f.write(nouveau_contenu)

# Verification finale
with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    v = f.read()

checks = {
    'boissons_bar':           'boissons_bar' in v,
    'categories_bar':         'categories_bar' in v,
    "name='Serveuse/Serveur'": "name='Serveuse/Serveur'" in v,
    'BoissonBar import':      "from bar.models import BoissonBar" in v,
}

print()
for key, ok in checks.items():
    print(f"  {'OK' if ok else 'MANQUANT'} — {key}")

if all(checks.values()):
    print()
    print("SUCCES TOTAL")
    print("=> Redemarrez le serveur Django")
    print("=> Ctrl+Shift+R dans le navigateur")
else:
    print()
    print("ERREUR - verifier le fichier")
