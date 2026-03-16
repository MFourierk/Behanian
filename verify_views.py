"""
Verification détaillée du views.py
"""
VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    v = f.read()

checks = {
    'boissons_bar':              'boissons_bar' in v,
    'categories_bar':            'categories_bar' in v,
    'CategorieBar':              'CategorieBar' in v,
    'Serveuse/Serveur':          'Serveuse/Serveur' in v,
    'exclude(categorie__id__in': 'exclude(categorie__id__in' in v,
}
for key, ok in checks.items():
    print(f"  {'OK' if ok else 'MANQUANT'} — {key}")

print()
# Afficher les lignes 751-820
lines = v.splitlines()
print("=== Lignes 748-820 ===")
for i, line in enumerate(lines[747:820], 748):
    print(f"L{i}: {line}")
