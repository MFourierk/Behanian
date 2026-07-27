# -*- coding: utf-8 -*-
"""
Initialise le catalogue plats gibier / volailles / poissons / brochettes.

Pour chaque plat :
  - Vérifie doublon (Plat.nom iexact)
  - Cherche l'ingrédient principal en base (icontains)
  - Si trouvé  → crée Plat + FicheTechnique + LigneFiche + PlatMenu
  - Si manquant → signale l'ingrédient à créer, crée le Plat sans fiche
"""
from django.core.management.base import BaseCommand
from cuisine.models import Plat, CategoriePlat, FicheTechnique, LigneFicheTechnique, Ingredient
from restaurant.models import PlatMenu, CategorieMenu

# ── Catalogue ───────────────────────────────────────────────────────────────
# (nom, prix_vente, cat_cuisine, ordre_cat, ingredient_recherche, nb_portions)
#
# ingredient_recherche : terme de recherche icontains dans Ingredient.nom
# nb_portions          : 1 = entier/pièce, 2 = demi, 4 = portion
# None                 = ingrédient à plusieurs composantes (signalement manuel)

CATALOGUE = [

    # ── GIBIERS ──────────────────────────────────────────────────────────
    ("Agouti Braisé Petit",         40000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Braisé Grand",         50000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Braisé Portion",       10000, "Gibiers", 10, "Agouti",      4),
    ("Agouti Soupe Petit",          40000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Soupe Grand",          50000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Soupe Portion",        10000, "Gibiers", 10, "Agouti",      4),
    ("Agouti Sauté Petit",          40000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Sauté Grand",          50000, "Gibiers", 10, "Agouti",      1),
    ("Agouti Sauté Portion",        10000, "Gibiers", 10, "Agouti",      4),

    ("Escargot Brochette",           5000, "Gibiers", 10, "Escargot",    1),
    ("Escargot Soupe",               5000, "Gibiers", 10, "Escargot",    1),
    ("Escargot Sauté",               5000, "Gibiers", 10, "Escargot",    1),

    ("Hérisson Braisé Petit",       40000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Braisé Grand",       50000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Braisé Portion",     10000, "Gibiers", 10, "Hérisson",    4),
    ("Hérisson Soupe Petit",        40000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Soupe Grand",        50000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Soupe Portion",      10000, "Gibiers", 10, "Hérisson",    4),
    ("Hérisson Sauté Petit",        40000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Sauté Grand",        50000, "Gibiers", 10, "Hérisson",    1),
    ("Hérisson Sauté Portion",      10000, "Gibiers", 10, "Hérisson",    4),

    ("Rat Braisé Petit",             6000, "Gibiers", 10, "Rat Palmiste", 1),  # fallback Rat si absent
    ("Rat Braisé Grand",             8000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Soupe Petit",              6000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Soupe Grand",              8000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Sauté Petit",              6000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Sauté Grand",              8000, "Gibiers", 10, "Rat Palmiste", 1),

    ("Rat Palmiste Braisé",          6000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Palmiste Soupe",           6000, "Gibiers", 10, "Rat Palmiste", 1),
    ("Rat Palmiste Sauté",           6000, "Gibiers", 10, "Rat Palmiste", 1),

    ("Pangolin Braisé Petit",       40000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Braisé Grand",       50000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Braisé Portion",      8000, "Gibiers", 10, "Pangolin",    4),
    ("Pangolin Soupe Petit",        40000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Soupe Grand",        50000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Soupe Portion",       8000, "Gibiers", 10, "Pangolin",    4),
    ("Pangolin Sauté Petit",        40000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Sauté Grand",        50000, "Gibiers", 10, "Pangolin",    1),
    ("Pangolin Sauté Portion",       8000, "Gibiers", 10, "Pangolin",    4),

    ("Lapin Braisé",                13000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Braisé Grand",          15000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Braisé Demi",            6500, "Gibiers", 10, "Lapin",       2),
    ("Lapin Soupe",                 13000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Soupe Grand",           15000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Soupe Demi",             6500, "Gibiers", 10, "Lapin",       2),
    ("Lapin Sauté",                 13000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Sauté Grand",           15000, "Gibiers", 10, "Lapin",       1),
    ("Lapin Sauté Demi",             6500, "Gibiers", 10, "Lapin",       2),

    # ── VOLAILLES ────────────────────────────────────────────────────────
    ("Pintade Braisée Entier",      12000, "Volailles", 20, "Pintade",         1),
    ("Pintade Braisée Demi",         6000, "Volailles", 20, "Pintade",         2),
    ("Pintade Soupe Entier",        12000, "Volailles", 20, "Pintade",         1),
    ("Pintade Soupe Demi",           6000, "Volailles", 20, "Pintade",         2),
    ("Pintade Sautée Entier",       12000, "Volailles", 20, "Pintade",         1),
    ("Pintade Sautée Demi",          6000, "Volailles", 20, "Pintade",         2),

    ("Poulet chair X Braisé",        7000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Braisé Demi",   3500, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair X Soupe",         7000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Soupe Demi",    3500, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair X Frit",          7000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Frit Demi",     3500, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair X Choukouya",     8000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Sauté",         8000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Rôti",          8000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair X Crème Mayo",    8000, "Volailles", 20, "Poulet de chair", 1),

    ("Poulet chair XX Braisé",      10000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Braisé Demi",  5000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XX Soupe",       10000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Soupe Demi",   5000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XX Frit",        10000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Frit Demi",    5000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XX Choukouya",   11000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Sauté",       11000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Rôti",        11000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XX Crème Mayo",  11000, "Volailles", 20, "Poulet de chair", 1),

    ("Poulet chair XXX Braisé",     12000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Braisé Demi", 6000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XXX Soupe",      12000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Soupe Demi",  6000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XXX Frit",       12000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Frit Demi",   6000, "Volailles", 20, "Poulet de chair", 2),
    ("Poulet chair XXX Choukouya",  13000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Sauté",      13000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Rôti",       13000, "Volailles", 20, "Poulet de chair", 1),
    ("Poulet chair XXX Crème Mayo", 13000, "Volailles", 20, "Poulet de chair", 1),

    ("Poulet pondeuse Braisé",       9000, "Volailles", 20, "Poulet pondeuse", 1),
    ("Poulet pondeuse Braisé Demi",  4500, "Volailles", 20, "Poulet pondeuse", 2),
    ("Poulet pondeuse Soupe",        9000, "Volailles", 20, "Poulet pondeuse", 1),
    ("Poulet pondeuse Soupe Demi",   4500, "Volailles", 20, "Poulet pondeuse", 2),
    ("Poulet pondeuse Sauté",        9000, "Volailles", 20, "Poulet pondeuse", 1),
    ("Poulet pondeuse Sauté Demi",   4500, "Volailles", 20, "Poulet pondeuse", 2),

    # ── BROCHETTES ───────────────────────────────────────────────────────
    ("Brochette de Mérou",          10000, "Brochettes", 30, "Mérou",          1),
    ("Brochette de Boeuf",           6000, "Brochettes", 30, "Boeuf",          1),
    ("Brochette de Gambas Sauté",   10000, "Brochettes", 30, "Gambas",         1),

    # ── POISSONS & FRUITS DE MER ─────────────────────────────────────────
    ("Carpe Braisée Petite",         9000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Braisée Grande",        17000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Soupe Petite",           9000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Soupe Grande",          17000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Sautée Petite",          9000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Sautée Grande",         17000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Frite Petite",           9000, "Poissons & Fruits de mer", 40, "Carpe",     1),
    ("Carpe Frite Grande",          17000, "Poissons & Fruits de mer", 40, "Carpe",     1),

    ("Sol Braisé Petit",             7000, "Poissons & Fruits de mer", 40, "Sol",       1),
    ("Sol Braisé Grand",            15000, "Poissons & Fruits de mer", 40, "Sol",       1),
    ("Sol Sauté Petit",              7000, "Poissons & Fruits de mer", 40, "Sol",       1),
    ("Sol Sauté Grand",             15000, "Poissons & Fruits de mer", 40, "Sol",       1),
    ("Sol Frit Petit",               7000, "Poissons & Fruits de mer", 40, "Sol",       1),
    ("Sol Frit Grand",              15000, "Poissons & Fruits de mer", 40, "Sol",       1),

    ("St Pierre Braisé Petit",       9000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Braisé Grand",      17000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Soupe Petit",        9000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Soupe Grand",       17000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Sauté Petit",        9000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Sauté Grand",       17000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Frit Petit",         9000, "Poissons & Fruits de mer", 40, "St Pierre", 1),
    ("St Pierre Frit Grand",        17000, "Poissons & Fruits de mer", 40, "St Pierre", 1),

    ("Crevette Sautée",              5000, "Poissons & Fruits de mer", 40, "Crevette",  1),
    ("Soupe de pêcheur",            20000, "Poissons & Fruits de mer", 40, None,        1),  # multi-ingrédients

    # ── SPÉCIALITÉS ──────────────────────────────────────────────────────
    ("Kedjénou du chasseur",        25000, "Spécialités", 50, None, 1),  # multi-ingrédients
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


def find_ingredient(terme):
    """Recherche flexible : exact d'abord, puis contains."""
    if not terme:
        return None
    ing = Ingredient.objects.filter(nom__iexact=terme, statut=True).first()
    if not ing:
        ing = Ingredient.objects.filter(nom__icontains=terme, statut=True).first()
    # Fallback Rat simple si Rat Palmiste absent
    if not ing and terme == "Rat Palmiste":
        ing = Ingredient.objects.filter(nom__icontains="Rat", statut=True).first()
    return ing


class Command(BaseCommand):
    help = "Initialise le catalogue plats (gibiers, volailles, poissons, brochettes) avec fiche technique"

    def handle(self, *args, **options):
        created = skipped = sans_fiche = 0
        manquants = set()

        cats_cuisine = {}
        cats_menu = {}

        for nom, prix, cat_nom, ordre, ing_terme, nb_portions in CATALOGUE:

            # Catégories (cache local)
            if cat_nom not in cats_cuisine:
                cats_cuisine[cat_nom] = get_cat_cuisine(cat_nom, ordre)
                cats_menu[cat_nom]    = get_cat_menu(cat_nom, ordre)
            cat_c = cats_cuisine[cat_nom]
            cat_m = cats_menu[cat_nom]

            # Vérification doublon Plat (insensible à la casse)
            existing_plat = Plat.objects.filter(nom__iexact=nom).first()
            if existing_plat:
                # Rattacher le PlatMenu orphelin si besoin
                pm = (PlatMenu.objects.filter(cuisine_plat_id=existing_plat.pk).first()
                      or PlatMenu.objects.filter(nom__iexact=nom).first())
                if pm and not pm.cuisine_plat_id:
                    pm.cuisine_plat_id = existing_plat.pk
                    pm.save(update_fields=['cuisine_plat_id'])
                skipped += 1
                continue

            # Recherche ingrédient principal
            ing = find_ingredient(ing_terme)
            if ing_terme and not ing:
                manquants.add(ing_terme)

            # ── Création FicheTechnique ───────────────────────────────────
            fiche = None
            if ing:
                fiche = FicheTechnique.objects.create(
                    nom=nom,
                    categorie=cat_c,
                    nb_portions=nb_portions,
                    statut='actif',
                )
                LigneFicheTechnique.objects.create(
                    fiche=fiche,
                    ingredient=ing,
                    quantite=1,  # 1 pièce — à ajuster selon la recette
                )
            else:
                sans_fiche += 1

            # ── Création Plat cuisine ─────────────────────────────────────
            plat = Plat.objects.create(
                nom=nom,
                categorie=cat_c,
                fiche_technique=fiche,
                prix_vente=prix,
                statut='disponible',
            )
            statut_ft = f"FT créée ({ing.nom})" if fiche else "⚠ sans FT (ingrédient manquant)"
            self.stdout.write(f"  + {nom} — {statut_ft}")

            # ── Création PlatMenu restaurant ──────────────────────────────
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

            created += 1

        # ── Rapport final ─────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"{created} plat(s) créé(s) — {skipped} déjà existant(s) — {sans_fiche} sans fiche technique."
        ))

        if manquants:
            self.stdout.write(self.style.WARNING(
                "\n⚠ Ingrédients MANQUANTS à créer dans Cuisine > Ingrédients :"
            ))
            for m in sorted(manquants):
                self.stdout.write(self.style.WARNING(f"   → {m}"))
            self.stdout.write(self.style.WARNING(
                "  Relancer cette commande après création pour générer les fiches techniques."
            ))
