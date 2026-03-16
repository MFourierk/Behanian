"""
Debug — vérifie ce que la vue restaurant_tpe envoie réellement
"""
import os, sys, django

sys.path.insert(0, r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from bar.models import BoissonBar, CategorieBar
from restaurant.models import CategorieMenu, PlatMenu
from django.contrib.auth.models import Group

print("=" * 50)
print("BOISSONS BAR")
print("=" * 50)
boissons = BoissonBar.objects.filter(disponible=True, statut='actif')
print(f"Nombre : {boissons.count()}")
for b in boissons:
    print(f"  [{b.id}] {b.nom} | cat={b.categorie.nom} | prix={b.prix} | stock={b.quantite_stock}")

print()
print("=" * 50)
print("CATEGORIES BAR")
print("=" * 50)
for c in CategorieBar.objects.all():
    print(f"  [{c.id}] {c.nom}")

print()
print("=" * 50)
print("CATEGORIES CUISINE (après filtre)")
print("=" * 50)
mots_boisson = ['boisson', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
categories_cuisine = [
    c for c in CategorieMenu.objects.all()
    if not any(m in c.nom.lower() for m in mots_boisson)
]
print(f"Nombre : {len(categories_cuisine)}")
for c in categories_cuisine:
    print(f"  [{c.id}] {c.nom}")

print()
print("=" * 50)
print("PLATS CUISINE")
print("=" * 50)
ids = [c.id for c in categories_cuisine]
plats = PlatMenu.objects.filter(disponible=True, categorie__id__in=ids) if ids else PlatMenu.objects.none()
print(f"Nombre : {plats.count()}")

print()
print("=" * 50)
print("SERVEURS (groupe 5)")
print("=" * 50)
try:
    g = Group.objects.get(id=5)
    serveurs = g.user_set.all()
    print(f"Groupe : {g.name}")
    print(f"Nombre : {serveurs.count()}")
    for u in serveurs:
        print(f"  {u.username} — {u.get_full_name()}")
except Group.DoesNotExist:
    print("Groupe 5 introuvable !")
    for g in Group.objects.all():
        print(f"  [{g.id}] {g.name} — {g.user_set.count()} users")
