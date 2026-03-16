"""
Diagnostic + patch automatique du restaurant views.py
"""
import re, sys

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    contenu = f.read()

# Diagnostic
print("=== DIAGNOSTIC ===")
print(f"'boissons_bar' dans views.py : {'OUI' if 'boissons_bar' in contenu else 'NON'}")
print(f"'categories_bar' dans views.py : {'OUI' if 'categories_bar' in contenu else 'NON'}")
print(f"'CategorieBar' dans views.py : {'OUI' if 'CategorieBar' in contenu else 'NON'}")

# Chercher la ligne exacte de restaurant_tpe
lines = contenu.splitlines()
for i, line in enumerate(lines, 1):
    if 'restaurant_tpe' in line:
        print(f"Ligne {i}: {line.strip()}")

print()

# Patch — remplacer le bloc def restaurant_tpe
NOUVELLE_FONCTION = '''@login_required
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

# Trouver le début et la fin de la fonction
pattern = re.compile(
    r'@login_required\s*\n\s*def restaurant_tpe\(request\):.*?return render\(request,\s*[\'"]restaurant/index\.html[\'"]\s*,\s*context\)\s*\n',
    re.DOTALL
)
match = pattern.search(contenu)

if match:
    # Backup
    with open(VIEWS_PATH + '.bak2', 'w', encoding='utf-8') as f:
        f.write(contenu)
    # Patch
    nouveau = contenu[:match.start()] + NOUVELLE_FONCTION + '\n' + contenu[match.end():]
    with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
        f.write(nouveau)
    print("OK views.py patche avec succes")
    print("Redemarrez le serveur Django")
else:
    print("ERREUR : fonction non trouvee par le pattern")
    print("Cherche manuellement autour de 'def restaurant_tpe'")
