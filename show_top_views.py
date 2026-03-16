"""
Affiche les lignes 20-50 du views.py pour trouver le conflit
"""
VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Lignes 1-50 ===")
for i, line in enumerate(lines[:50], 1):
    print(f"L{i:3}: {line.rstrip()}")
