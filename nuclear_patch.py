"""
Patch nuclear — reécrit restaurant_tpe ligne par ligne
"""
import os

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver la ligne exacte de def restaurant_tpe
debut_def = None
for i, line in enumerate(lines):
    if 'def restaurant_tpe(request):' in line:
        debut_def = i
        print(f"Trouve 'def restaurant_tpe' a la ligne {i+1}")
        break

if debut_def is None:
    print("ERREUR: def restaurant_tpe introuvable!")
    exit(1)

# Le @login_required est-il juste avant ?
debut = debut_def
if debut_def > 0 and '@login_required' in lines[debut_def - 1]:
    debut = debut_def - 1
    print(f"@login_required trouve ligne {debut+1}")

# Trouver la fin — prochaine fonction/classe au niveau 0
fin = None
for i in range(debut_def + 5, len(lines)):
    line = lines[i]
    # Ligne non vide qui commence au niveau 0 avec def/class/@
    if line and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('\n') and not line.startswith('#'):
        fin = i
        print(f"Fin trouvee ligne {fin+1}: {line.rstrip()}")
        break

if fin is None:
    fin = len(lines)
    print(f"Fin = fin du fichier")

print(f"Bloc a remplacer: lignes {debut+1} a {fin}")
print(f"Nombre de lignes actuelles: {fin - debut}")

# Afficher les 3 premieres et 3 dernieres lignes du bloc actuel
print("\nDebut actuel:")
for l in lines[debut:debut+3]:
    print(f"  {l.rstrip()}")
print("Fin actuelle:")
for l in lines[fin-3:fin]:
    print(f"  {l.rstrip()}")

# Backup
backup = VIEWS_PATH + '.nuclear_bak'
with open(backup, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"\nBackup: {backup}")

# Nouvelle fonction
NOUVELLE_FONCTION = [
    '@login_required\n',
    'def restaurant_tpe(request):\n',
    '    """Interface TPE Restaurant"""\n',
    '    from bar.models import BoissonBar, CategorieBar\n',
    '    from django.contrib.auth.models import User, Group\n',
    '    from dashboard.models import Configuration\n',
    '\n',
    '    # Boissons Cave\n',
    '    boissons_bar = BoissonBar.objects.select_related("categorie").filter(\n',
    '        statut="actif", disponible=True\n',
    '    ).order_by("categorie__nom", "nom")\n',
    '    categories_bar = CategorieBar.objects.order_by("nom")\n',
    '\n',
    '    # Plats Cuisine\n',
    '    mots_boisson = ["boisson", "biere", "vin", "alcool", "soda", "jus", "soft", "liqueur", "spiritueux"]\n',
    '    categories_cuisine = [\n',
    '        c for c in CategorieMenu.objects.all()\n',
    '        if not any(m in c.nom.lower() for m in mots_boisson)\n',
    '    ]\n',
    '    ids_cuisine = [c.id for c in categories_cuisine]\n',
    '    plats = PlatMenu.objects.filter(\n',
    '        disponible=True, categorie__id__in=ids_cuisine\n',
    '    ).select_related("categorie") if ids_cuisine else PlatMenu.objects.none()\n',
    '\n',
    '    for plat in plats:\n',
    '        plat.en_stock = True\n',
    '        plat.stock_quantity = 999\n',
    '\n',
    '    for b in boissons_bar:\n',
    '        b.stock_quantity = int(b.quantite_stock)\n',
    '\n',
    '    # Serveurs\n',
    '    try:\n',
    '        groupe_serveurs = Group.objects.get(name="Serveuse/Serveur")\n',
    '        serveurs = User.objects.filter(\n',
    '            groups=groupe_serveurs, is_active=True\n',
    '        ).order_by("first_name", "last_name", "username")\n',
    '    except Group.DoesNotExist:\n',
    '        serveurs = User.objects.none()\n',
    '\n',
    '    tables = Table.objects.all()\n',
    '    commandes_en_cours_list = Commande.objects.filter(\n',
    '        statut__in=["en_attente", "en_preparation", "prete", "servie"]\n',
    '    ).order_by("-date_modification").prefetch_related("lignes", "table")\n',
    '    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)\n',
    '    config = Configuration.load()\n',
    '\n',
    '    context = {\n',
    '        "categories":         CategorieMenu.objects.all(),\n',
    '        "plats":              plats,\n',
    '        "categories_cuisine": categories_cuisine,\n',
    '        "categories_bar":     categories_bar,\n',
    '        "boissons_bar":       boissons_bar,\n',
    '        "tables":             tables,\n',
    '        "accompagnements":    accompagnements,\n',
    '        "commandes_en_cours": commandes_en_cours_list.count(),\n',
    '        "commandes_en_cours_list": commandes_en_cours_list,\n',
    '        "config":             config,\n',
    '        "serveurs":           serveurs,\n',
    '    }\n',
    '    return render(request, "restaurant/index.html", context)\n',
    '\n',
    '\n',
]

# Construire le nouveau fichier
nouveau = lines[:debut] + NOUVELLE_FONCTION + lines[fin:]

with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
    f.writelines(nouveau)

# Verification
with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    v = f.read()

print("\n=== VERIFICATION ===")
checks = {
    'boissons_bar':            'boissons_bar' in v,
    'categories_bar':          'categories_bar' in v,
    'BoissonBar':              'from bar.models import BoissonBar' in v,
    'Serveuse/Serveur':        'Serveuse/Serveur' in v,
    'restaurant/index.html':   'restaurant/index.html' in v,
}
all_ok = True
for key, ok in checks.items():
    status = 'OK' if ok else 'MANQUANT'
    if not ok:
        all_ok = False
    print(f"  {status} — {key}")

print()
if all_ok:
    print("SUCCES — Redemarrez le serveur Django maintenant")
else:
    print("ERREUR — certains elements manquent")
