"""
Force patch — remplace restaurant_tpe directement par numero de ligne
"""
import os

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver debut et fin de restaurant_tpe
debut = None
fin = None
for i, line in enumerate(lines):
    if 'def restaurant_tpe(request):' in line:
        # Chercher le @login_required juste avant
        debut = i - 1 if i > 0 and '@login_required' in lines[i-1] else i
        print(f"Debut trouve ligne {debut+1}: {lines[debut].rstrip()}")
    if debut is not None and fin is None and i > debut + 5:
        # Fin = prochaine fonction de niveau 0 apres restaurant_tpe
        if (line.startswith('def ') or line.startswith('@') or line.startswith('class ')) and i > debut + 10:
            fin = i
            print(f"Fin trouvee ligne {fin+1}: {lines[fin].rstrip()}")
            break

if debut is None:
    print("ERREUR: def restaurant_tpe introuvable")
    exit(1)

if fin is None:
    fin = len(lines)
    print(f"Fin = fin du fichier ligne {fin}")

print(f"Bloc a remplacer : lignes {debut+1} a {fin}")
print()

# Nouvelle fonction
NOUVELLE = '''@login_required
def restaurant_tpe(request):
    """Interface TPE Restaurant"""
    from dashboard.models import Configuration
    from bar.models import CategorieBar

    mots_boisson = ['boisson', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
    categories_cuisine = [
        c for c in CategorieMenu.objects.all()
        if not any(m in c.nom.lower() for m in mots_boisson)
    ]
    categories_bar = CategorieBar.objects.all().order_by('nom')
    ids_cat_cuisine = [c.id for c in categories_cuisine]
    plats = PlatMenu.objects.filter(
        disponible=True, categorie__id__in=ids_cat_cuisine
    ) if ids_cat_cuisine else PlatMenu.objects.none()

    boissons_bar = BoissonBar.objects.filter(
        disponible=True, statut='actif'
    ).select_related('categorie').order_by('categorie__nom', 'nom')

    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
    ).order_by('-date_modification').prefetch_related('lignes', 'table')
    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)
    config = Configuration.load()

    for plat in plats:
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available
        if hasattr(plat, 'fiche_technique'):
            plat.stock_quantity = plat.fiche_technique.max_portions_possibles()
        else:
            try:
                from cuisine.models import Ingredient
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                plat.stock_quantity = int(ing.quantite_stock) if ing else 999
            except:
                plat.stock_quantity = 999

    for b in boissons_bar:
        b.stock_quantity = int(b.quantite_stock)

    from django.contrib.auth.models import Group
    try:
        serveurs = Group.objects.get(id=5).user_set.all().order_by('first_name', 'username')
    except:
        serveurs = []

    context = {
        'categories': CategorieMenu.objects.all(),
        'plats': plats,
        'categories_cuisine': categories_cuisine,
        'categories_bar': categories_bar,
        'boissons_bar': boissons_bar,
        'tables': tables,
        'accompagnements': accompagnements,
        'commandes_en_cours': commandes_en_cours_list.count(),
        'commandes_en_cours_list': commandes_en_cours_list,
        'config': config,
        'serveurs': serveurs,
    }
    return render(request, 'restaurant/index.html', context)

'''

# Backup
with open(VIEWS_PATH + '.bak3', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Backup cree: views.py.bak3")

# Nouveau contenu
nouveau = lines[:debut] + [NOUVELLE] + lines[fin:]
with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
    f.writelines(nouveau)

# Verification
with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()

ok_boissons  = 'boissons_bar' in verify
ok_categories = 'categories_bar' in verify
ok_serveurs  = "Group.objects.get(id=5)" in verify

print(f"boissons_bar present  : {'OK' if ok_boissons else 'MANQUANT'}")
print(f"categories_bar present: {'OK' if ok_categories else 'MANQUANT'}")
print(f"serveurs present      : {'OK' if ok_serveurs else 'MANQUANT'}")

if ok_boissons and ok_categories and ok_serveurs:
    print()
    print("SUCCES - Redemarrez le serveur Django")
else:
    print()
    print("ERREUR - Certains elements manquent")
