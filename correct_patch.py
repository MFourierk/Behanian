"""
Patch final correct — la vue restaurant_tpe utilise
directement BoissonBar et CategorieBar comme la Cave
ET sépare les plats cuisine des boissons
"""
import os

VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver restaurant_tpe
debut_def = None
for i, line in enumerate(lines):
    if 'def restaurant_tpe(request):' in line:
        debut_def = i
        break

debut = debut_def - 1 if debut_def > 0 and '@login_required' in lines[debut_def-1] else debut_def

# Trouver fin
fin = len(lines)
for i in range(debut_def + 5, len(lines)):
    line = lines[i]
    if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
        fin = i
        break

print(f"Remplacement lignes {debut+1} a {fin}")

# Backup
with open(VIEWS_PATH + '.correct_bak', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Nouvelle fonction — utilise DIRECTEMENT CategorieBar/BoissonBar
NOUVELLE = '''\
@login_required
def restaurant_tpe(request):
    """Interface TPE Restaurant"""
    from bar.models import BoissonBar, CategorieBar
    from django.contrib.auth.models import User, Group
    from dashboard.models import Configuration

    # ── Boissons directement depuis la Cave (comme bar_tpe) ──
    boissons_bar = BoissonBar.objects.select_related("categorie").filter(
        statut="actif", disponible=True
    ).order_by("categorie__nom", "nom")
    categories_bar = CategorieBar.objects.order_by("nom")

    for b in boissons_bar:
        b.stock_quantity = int(b.quantite_stock)

    # ── Plats cuisine — EXCLURE la catégorie "Boissons" ──
    cat_boissons_ids = list(
        CategorieMenu.objects.filter(nom__icontains="boisson").values_list("id", flat=True)
    )
    plats = PlatMenu.objects.filter(disponible=True).exclude(
        categorie__id__in=cat_boissons_ids
    ).select_related("categorie")

    categories_cuisine = list(
        CategorieMenu.objects.exclude(id__in=cat_boissons_ids)
    )

    for plat in plats:
        plat.en_stock = True
        plat.stock_quantity = 999
        try:
            is_available, _ = check_stock_availability(plat, 1)
            plat.en_stock = is_available
        except Exception:
            pass

    # ── Serveurs (comme bar_tpe) ──
    try:
        groupe_serveurs = Group.objects.get(name="Serveuse/Serveur")
        serveurs = User.objects.filter(
            groups=groupe_serveurs, is_active=True
        ).order_by("first_name", "last_name", "username")
    except Group.DoesNotExist:
        serveurs = User.objects.none()

    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=["en_attente", "en_preparation", "prete", "servie"]
    ).order_by("-date_modification").prefetch_related("lignes", "table")
    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)
    config = Configuration.load()

    context = {
        "categories":             CategorieMenu.objects.all(),
        "plats":                  plats,
        "categories_cuisine":     categories_cuisine,
        "categories_bar":         categories_bar,
        "boissons_bar":           boissons_bar,
        "tables":                 tables,
        "accompagnements":        accompagnements,
        "commandes_en_cours":     commandes_en_cours_list.count(),
        "commandes_en_cours_list": commandes_en_cours_list,
        "config":                 config,
        "serveurs":               serveurs,
    }
    return render(request, "restaurant/index.html", context)

'''

nouveau = lines[:debut] + [NOUVELLE] + lines[fin:]

with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
    f.writelines(nouveau)

# Vérification
with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    v = f.read()

print("\n=== VERIFICATION ===")
ok = all([
    'boissons_bar' in v,
    'categories_bar' in v,
    'CategorieBar' in v,
    'Serveuse/Serveur' in v,
    'exclude(categorie__id__in' in v,
])
print("SUCCES" if ok else "ERREUR")
print("\nRedemarrez le serveur Django")
print("Puis Ctrl+Shift+R dans le navigateur")
