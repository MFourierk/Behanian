"""
Ajoute une route de debug temporaire dans restaurant/urls.py
pour voir exactement ce que Django envoie au template
"""
import os, sys

PROJECT = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"

# 1. Lire urls.py restaurant
urls_path = os.path.join(PROJECT, 'restaurant', 'urls.py')
with open(urls_path, 'r', encoding='utf-8') as f:
    urls = f.read()

print("=== urls.py restaurant ===")
print(urls)
print()

# 2. Lire les 30 premieres lignes de views.py pour voir les imports
views_path = os.path.join(PROJECT, 'restaurant', 'views.py')
with open(views_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver restaurant_tpe et afficher les 60 lignes suivantes
for i, line in enumerate(lines):
    if 'def restaurant_tpe' in line:
        print(f"=== views.py — restaurant_tpe (ligne {i+1}) ===")
        print(''.join(lines[i:i+60]))
        break
