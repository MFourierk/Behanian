# -*- coding: utf-8 -*-
"""
Initialise le catalogue plats gibier / volailles / poissons / brochettes.
- Vérifie les doublons par nom (insensible à la casse) avant création
- Crée le Plat cuisine ET le PlatMenu restaurant (avec cuisine_plat_id)
- Ne touche pas aux plats existants
"""
from django.core.management.base import BaseCommand
from cuisine.models import Plat, CategoriePlat
from restaurant.models import PlatMenu, CategorieMenu

# (nom, prix_vente, cat_cuisine, ordre_cat)
CATALOGUE = [

    # ── GIBIERS ──────────────────────────────────────────────────────────
    ("Agouti Braisé Petit",         40000, "Gibiers", 10),
    ("Agouti Braisé Grand",         50000, "Gibiers", 10),
    ("Agouti Braisé Portion",       10000, "Gibiers", 10),
    ("Agouti Soupe Petit",          40000, "Gibiers", 10),
    ("Agouti Soupe Grand",          50000, "Gibiers", 10),
    ("Agouti Soupe Portion",        10000, "Gibiers", 10),
    ("Agouti Sauté Petit",          40000, "Gibiers", 10),
    ("Agouti Sauté Grand",          50000, "Gibiers", 10),
    ("Agouti Sauté Portion",        10000, "Gibiers", 10),

    ("Escargot Brochette",           5000, "Gibiers", 10),
    ("Escargot Soupe",               5000, "Gibiers", 10),
    ("Escargot Sauté",               5000, "Gibiers", 10),

    ("Hérisson Braisé Petit",       40000, "Gibiers", 10),
    ("Hérisson Braisé Grand",       50000, "Gibiers", 10),
    ("Hérisson Braisé Portion",     10000, "Gibiers", 10),
    ("Hérisson Soupe Petit",        40000, "Gibiers", 10),
    ("Hérisson Soupe Grand",        50000, "Gibiers", 10),
    ("Hérisson Soupe Portion",      10000, "Gibiers", 10),
    ("Hérisson Sauté Petit",        40000, "Gibiers", 10),
    ("Hérisson Sauté Grand",        50000, "Gibiers", 10),
    ("Hérisson Sauté Portion",      10000, "Gibiers", 10),

    ("Rat Braisé Petit",             6000, "Gibiers", 10),
    ("Rat Braisé Grand",             8000, "Gibiers", 10),
    ("Rat Soupe Petit",              6000, "Gibiers", 10),
    ("Rat Soupe Grand",              8000, "Gibiers", 10),
    ("Rat Sauté Petit",              6000, "Gibiers", 10),
    ("Rat Sauté Grand",              8000, "Gibiers", 10),

    ("Rat Palmiste Braisé",          6000, "Gibiers", 10),
    ("Rat Palmiste Soupe",           6000, "Gibiers", 10),
    ("Rat Palmiste Sauté",           6000, "Gibiers", 10),

    ("Pangolin Braisé Petit",       40000, "Gibiers", 10),
    ("Pangolin Braisé Grand",       50000, "Gibiers", 10),
    ("Pangolin Braisé Portion",      8000, "Gibiers", 10),
    ("Pangolin Soupe Petit",        40000, "Gibiers", 10),
    ("Pangolin Soupe Grand",        50000, "Gibiers", 10),
    ("Pangolin Soupe Portion",       8000, "Gibiers", 10),
    ("Pangolin Sauté Petit",        40000, "Gibiers", 10),
    ("Pangolin Sauté Grand",        50000, "Gibiers", 10),
    ("Pangolin Sauté Portion",       8000, "Gibiers", 10),

    ("Lapin Braisé",                13000, "Gibiers", 10),
    ("Lapin Braisé Grand",          15000, "Gibiers", 10),
    ("Lapin Braisé Demi",            6500, "Gibiers", 10),
    ("Lapin Soupe",                 13000, "Gibiers", 10),
    ("Lapin Soupe Grand",           15000, "Gibiers", 10),
    ("Lapin Soupe Demi",             6500, "Gibiers", 10),
    ("Lapin Sauté",                 13000, "Gibiers", 10),
    ("Lapin Sauté Grand",           15000, "Gibiers", 10),
    ("Lapin Sauté Demi",             6500, "Gibiers", 10),

    # ── VOLAILLES ────────────────────────────────────────────────────────
    ("Pintade Braisée Entier",      12000, "Volailles", 20),
    ("Pintade Braisée Demi",         6000, "Volailles", 20),
    ("Pintade Soupe Entier",        12000, "Volailles", 20),
    ("Pintade Soupe Demi",           6000, "Volailles", 20),
    ("Pintade Sautée Entier",       12000, "Volailles", 20),
    ("Pintade Sautée Demi",          6000, "Volailles", 20),

    ("Poulet chair X Braisé",        7000, "Volailles", 20),
    ("Poulet chair X Braisé Demi",   3500, "Volailles", 20),
    ("Poulet chair X Soupe",         7000, "Volailles", 20),
    ("Poulet chair X Soupe Demi",    3500, "Volailles", 20),
    ("Poulet chair X Frit",          7000, "Volailles", 20),
    ("Poulet chair X Frit Demi",     3500, "Volailles", 20),
    ("Poulet chair X Choukouya",     8000, "Volailles", 20),
    ("Poulet chair X Sauté",         8000, "Volailles", 20),
    ("Poulet chair X Rôti",          8000, "Volailles", 20),
    ("Poulet chair X Crème Mayo",    8000, "Volailles", 20),

    ("Poulet chair XX Braisé",      10000, "Volailles", 20),
    ("Poulet chair XX Braisé Demi",  5000, "Volailles", 20),
    ("Poulet chair XX Soupe",       10000, "Volailles", 20),
    ("Poulet chair XX Soupe Demi",   5000, "Volailles", 20),
    ("Poulet chair XX Frit",        10000, "Volailles", 20),
    ("Poulet chair XX Frit Demi",    5000, "Volailles", 20),
    ("Poulet chair XX Choukouya",   11000, "Volailles", 20),
    ("Poulet chair XX Sauté",       11000, "Volailles", 20),
    ("Poulet chair XX Rôti",        11000, "Volailles", 20),
    ("Poulet chair XX Crème Mayo",  11000, "Volailles", 20),

    ("Poulet chair XXX Braisé",     12000, "Volailles", 20),
    ("Poulet chair XXX Braisé Demi", 6000, "Volailles", 20),
    ("Poulet chair XXX Soupe",      12000, "Volailles", 20),
    ("Poulet chair XXX Soupe Demi",  6000, "Volailles", 20),
    ("Poulet chair XXX Frit",       12000, "Volailles", 20),
    ("Poulet chair XXX Frit Demi",   6000, "Volailles", 20),
    ("Poulet chair XXX Choukouya",  13000, "Volailles", 20),
    ("Poulet chair XXX Sauté",      13000, "Volailles", 20),
    ("Poulet chair XXX Rôti",       13000, "Volailles", 20),
    ("Poulet chair XXX Crème Mayo", 13000, "Volailles", 20),

    ("Poulet pondeuse Braisé",       9000, "Volailles", 20),
    ("Poulet pondeuse Braisé Demi",  4500, "Volailles", 20),
    ("Poulet pondeuse Soupe",        9000, "Volailles", 20),
    ("Poulet pondeuse Soupe Demi",   4500, "Volailles", 20),
    ("Poulet pondeuse Sauté",        9000, "Volailles", 20),
    ("Poulet pondeuse Sauté Demi",   4500, "Volailles", 20),

    # ── BROCHETTES ───────────────────────────────────────────────────────
    ("Brochette de Mérou",          10000, "Brochettes", 30),
    ("Brochette de Boeuf",           6000, "Brochettes", 30),
    ("Brochette de Gambas Sauté",   10000, "Brochettes", 30),

    # ── POISSONS & FRUITS DE MER ─────────────────────────────────────────
    ("Carpe Braisée Petite",         9000, "Poissons & Fruits de mer", 40),
    ("Carpe Braisée Grande",        17000, "Poissons & Fruits de mer", 40),
    ("Carpe Soupe Petite",           9000, "Poissons & Fruits de mer", 40),
    ("Carpe Soupe Grande",          17000, "Poissons & Fruits de mer", 40),
    ("Carpe Sautée Petite",          9000, "Poissons & Fruits de mer", 40),
    ("Carpe Sautée Grande",         17000, "Poissons & Fruits de mer", 40),
    ("Carpe Frite Petite",           9000, "Poissons & Fruits de mer", 40),
    ("Carpe Frite Grande",          17000, "Poissons & Fruits de mer", 40),

    ("Sol Braisé Petit",             7000, "Poissons & Fruits de mer", 40),
    ("Sol Braisé Grand",            15000, "Poissons & Fruits de mer", 40),
    ("Sol Sauté Petit",              7000, "Poissons & Fruits de mer", 40),
    ("Sol Sauté Grand",             15000, "Poissons & Fruits de mer", 40),
    ("Sol Frit Petit",               7000, "Poissons & Fruits de mer", 40),
    ("Sol Frit Grand",              15000, "Poissons & Fruits de mer", 40),

    ("St Pierre Braisé Petit",       9000, "Poissons & Fruits de mer", 40),
    ("St Pierre Braisé Grand",      17000, "Poissons & Fruits de mer", 40),
    ("St Pierre Soupe Petit",        9000, "Poissons & Fruits de mer", 40),
    ("St Pierre Soupe Grand",       17000, "Poissons & Fruits de mer", 40),
    ("St Pierre Sauté Petit",        9000, "Poissons & Fruits de mer", 40),
    ("St Pierre Sauté Grand",       17000, "Poissons & Fruits de mer", 40),
    ("St Pierre Frit Petit",         9000, "Poissons & Fruits de mer", 40),
    ("St Pierre Frit Grand",        17000, "Poissons & Fruits de mer", 40),

    ("Crevette Sautée",              5000, "Poissons & Fruits de mer", 40),
    ("Soupe de pêcheur",            20000, "Poissons & Fruits de mer", 40),

    # ── SPÉCIALITÉS ──────────────────────────────────────────────────────
    ("Kedjénou du chasseur",        25000, "Spécialités", 50),
]


def get_cat_cuisine(nom, ordre):
    cat = CategoriePlat.objects.filter(nom__iexact=nom).first()
    if not cat:
        cat = CategoriePlat.objects.create(nom=nom, ordre=ordre)
    return cat


def get_cat_menu(nom, ordre):
    cat = CategorieMenu.objects.filter(nom__iexact=nom).first()
    if not cat:
        cat = CategorieMenu.objects.create(nom=nom, ordre=ordre)
    return cat


class Command(BaseCommand):
    help = "Initialise le catalogue plats (gibiers, volailles, poissons, brochettes) sans doublon"

    def handle(self, *args, **options):
        created = skipped = 0

        cats_cuisine = {}
        cats_menu = {}

        for nom, prix, cat_nom, ordre in CATALOGUE:
            # Catégories (cache local)
            if cat_nom not in cats_cuisine:
                cats_cuisine[cat_nom] = get_cat_cuisine(cat_nom, ordre)
                cats_menu[cat_nom]    = get_cat_menu(cat_nom, ordre)
            cat_c = cats_cuisine[cat_nom]
            cat_m = cats_menu[cat_nom]

            # Vérification doublon cuisine (insensible à la casse)
            existing_plat = Plat.objects.filter(nom__iexact=nom).first()
            if existing_plat:
                # Vérifier/rattacher le PlatMenu si orphelin
                pm = PlatMenu.objects.filter(cuisine_plat_id=existing_plat.pk).first()
                if not pm:
                    pm = PlatMenu.objects.filter(nom__iexact=nom).first()
                    if pm and not pm.cuisine_plat_id:
                        pm.cuisine_plat_id = existing_plat.pk
                        pm.save(update_fields=['cuisine_plat_id'])
                skipped += 1
                continue

            # Création du Plat cuisine
            plat = Plat.objects.create(
                nom=nom,
                categorie=cat_c,
                prix_vente=prix,
                statut='disponible',
            )
            self.stdout.write(f"  + [Cuisine] {nom} ({prix:,} F)")

            # Vérification doublon restaurant avant création
            pm_existing = (
                PlatMenu.objects.filter(cuisine_plat_id=plat.pk).first()
                or PlatMenu.objects.filter(nom__iexact=nom).first()
            )
            if pm_existing:
                if not pm_existing.cuisine_plat_id:
                    pm_existing.cuisine_plat_id = plat.pk
                    pm_existing.save(update_fields=['cuisine_plat_id'])
            else:
                PlatMenu.objects.create(
                    nom=nom,
                    categorie=cat_m,
                    prix=prix,
                    disponible=True,
                    cuisine_plat_id=plat.pk,
                    temps_preparation=15,
                )
                self.stdout.write(f"  + [Resto]   {nom}")

            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n{created} plat(s) créé(s), {skipped} déjà existant(s) — aucun doublon."
        ))
