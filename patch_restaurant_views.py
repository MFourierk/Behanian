"""
Script de patch — remplace la fonction restaurant_tpe dans views.py
Exécuter : python patch_restaurant_views.py
"""
import re, os

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

NOUVELLE_FONCTION = '''@login_required
def restaurant_tpe(request):
    """Interface TPE Restaurant"""
    from dashboard.models import Configuration
    from bar.models import CategorieBar

    # Catégories CUISINE (exclure boissons)
    mots_boisson = ['boisson', 'bière', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
    categories_cuisine = [
        c for c in CategorieMenu.objects.all()
        if not any(m in c.nom.lower() for m in mots_boisson)
    ]

    # Catégories BAR (Cave)
    categories_bar = CategorieBar.objects.all().order_by('nom')

    # Plats CUISINE uniquement
    ids_cat_cuisine = [c.id for c in categories_cuisine]
    plats = PlatMenu.objects.filter(
        disponible=True,
        categorie__id__in=ids_cat_cuisine
    ) if ids_cat_cuisine else PlatMenu.objects.none()

    # Boissons de la Cave
    boissons_bar = BoissonBar.objects.filter(
        disponible=True, statut='actif'
    ).select_related('categorie').order_by('categorie__nom', 'nom')

    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
    ).order_by('-date_modification').prefetch_related('lignes', 'table')
    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)
    config = Configuration.load()

    # Stock plats
    for plat in plats:
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available
        if hasattr(plat, 'fiche_technique'):
            plat.stock_quantity = plat.fiche_technique.max_portions_possibles()
        else:
            try:
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                plat.stock_quantity = int(ing.quantite_stock) if ing else 999
            except:
                plat.stock_quantity = 999

    # Stock boissons
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

# Lire le fichier
with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    contenu = f.read()

# Trouver et remplacer la fonction restaurant_tpe
pattern = r'(@login_required\s*\ndef restaurant_tpe\(request\):.*?return render\(request,\s*[\'"]restaurant/index\.html[\'"]\s*,\s*context\)\s*\n)'
match = re.search(pattern, contenu, re.DOTALL)

if match:
    # Sauvegarde
    backup_path = VIEWS_PATH + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"Backup créé : {backup_path}")

    # Remplacement
    nouveau_contenu = contenu[:match.start()] + NOUVELLE_FONCTION + '\n' + contenu[match.end():]
    with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
        f.write(nouveau_contenu)
    print("✅ views.py patché avec succès !")
    print("👉 Redémarrez le serveur Django")
else:
    print("❌ Fonction restaurant_tpe non trouvée — vérifiez le fichier")
    # Afficher les 5 premières occurrences de 'restaurant_tpe' pour debug
    for i, line in enumerate(contenu.splitlines(), 1):
        if 'restaurant_tpe' in line:
            print(f"  Ligne {i}: {line.strip()}")
