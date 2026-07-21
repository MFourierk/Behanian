# -*- coding: utf-8 -*-
"""
Initialise / met a jour le catalogue boissons de la Cave.
- update_or_create par nom (insensible a la casse) -> pas de doublon
- Ne crase pas le prix_achat si deja renseigne et > 0
- Ne touche pas aux prix de vente, stock, ni aux autres champs
"""
import math
from django.core.management.base import BaseCommand
from bar.models import BoissonBar, CategorieBar


def arrondi5(v):
    """Arrondi au multiple de 5 le plus proche (0.5 vers le haut)."""
    if not v:
        return 0
    return int(math.floor((v + 2.5) / 5) * 5)


def get_cat(nom, ordre):
    cat = CategorieBar.objects.filter(nom__iexact=nom).first()
    if not cat:
        cat = CategorieBar.objects.create(nom=nom, ordre=ordre)
    return cat


# (nom, prix_achat_unitaire, categorie, unite_standard)
CATALOGUE = [
    # ── Softs & Eaux ─────────────────────────────────────────
    ("Tonic",           190,    "Softs & Eaux",        "canette"),
    ("Coca Cola",       225,    "Softs & Eaux",        "canette"),
    ("Sprite",          185,    "Softs & Eaux",        "canette"),
    ("Fanta Orange",    195,    "Softs & Eaux",        "canette"),
    ("Fanta Citron",    225,    "Softs & Eaux",        "canette"),
    ("Orangina",        305,    "Softs & Eaux",        "bouteille"),
    ("Agrume",          290,    "Softs & Eaux",        "canette"),
    ("Kirene 1,5L",     290,    "Softs & Eaux",        "bouteille"),
    ("Awa",               0,    "Softs & Eaux",        "bouteille"),
    ("Olgane",            0,    "Softs & Eaux",        "bouteille"),
    ("Jus",             460,    "Softs & Eaux",        "bouteille"),
    ("Malta",            65,    "Softs & Eaux",        "bouteille"),
    ("Doppel Energy",   315,    "Softs & Eaux",        "canette"),
    ("Celeste",         235,    "Softs & Eaux",        "bouteille"),

    # ── Bieres ───────────────────────────────────────────────
    ("Heineken",        480,    "Bieres",              "bouteille"),
    ("Beaufort",        440,    "Bieres",              "bouteille"),
    ("Doppel",          315,    "Bieres",              "bouteille"),
    ("Desperados",      480,    "Bieres",              "bouteille"),
    ("Codys",           395,    "Bieres",              "bouteille"),
    ("Guiness",         645,    "Bieres",              "bouteille"),
    ("Bavaria",         135,    "Bieres",              "canette"),
    ("Bock",            285,    "Bieres",              "bouteille"),
    ("Sanbitter",       665,    "Bieres",              "bouteille"),
    ("Budweiser",       625,    "Bieres",              "canette"),
    ("Castel",          390,    "Bieres",              "bouteille"),
    ("Rhino",           315,    "Bieres",              "bouteille"),

    # ── Vins ─────────────────────────────────────────────────
    ("Valpierre",          1710,  "Vins",              "bouteille"),
    ("Cote du Rhone",       500,  "Vins",              "bouteille"),
    ("Arignac Blanc",      2415,  "Vins",              "bouteille"),
    ("Arignac Rouge Moelleux", 2415, "Vins",           "bouteille"),
    ("Arignac Rouge Sec",   250,  "Vins",              "bouteille"),
    ("Cuvee",              1835,  "Vins",              "bouteille"),
    ("Muscador",           2500,  "Vins",              "bouteille"),
    ("Hausman",             550,  "Vins",              "bouteille"),
    ("Deux Ages",          2835,  "Vins",              "bouteille"),
    ("Probus",             2300,  "Vins",              "bouteille"),
    ("Chemindepp",          465,  "Vins",              "bouteille"),
    ("Calvet",              485,  "Vins",              "bouteille"),
    ("Muscalon",            250,  "Vins",              "bouteille"),
    ("Chenet Blanc",       3250,  "Vins",              "bouteille"),
    ("Huit Clos",          2665,  "Vins",              "bouteille"),
    ("Mouton Cadet",       6085,  "Vins",              "bouteille"),
    ("Baron Del Lugar",    1835,  "Vins",              "bouteille"),
    ("Chamberi Blanc",     1585,  "Vins",              "bouteille"),
    ("Chamberi Rouge",     1585,  "Vins",              "bouteille"),
    ("Bois Chantant",      5750,  "Vins",              "bouteille"),
    ("RLG Rouge",          1835,  "Vins",              "bouteille"),
    ("RLG Blanc",          1835,  "Vins",              "bouteille"),

    # ── Champagnes & Mousseux ─────────────────────────────────
    ("Arignac Mousseux",   3165,  "Champagnes & Mousseux", "bouteille"),
    ("Laurent Perrier",   24000,  "Champagnes & Mousseux", "bouteille"),
]

CAT_ORDRE = {
    "Softs & Eaux":          1,
    "Bieres":                2,
    "Vins":                  3,
    "Champagnes & Mousseux": 4,
}


class Command(BaseCommand):
    help = "Initialise ou met a jour le catalogue boissons Cave (sans doublon)"

    def handle(self, *args, **options):
        created = updated = skipped = 0

        cats = {nom: get_cat(nom, ordre) for nom, ordre in CAT_ORDRE.items()}

        for nom, prix_achat, cat_nom, unite in CATALOGUE:
            cat = cats[cat_nom]

            # Recherche insensible a la casse
            existing = BoissonBar.objects.filter(nom__iexact=nom).first()

            if existing:
                changed = False
                # Met a jour le prix_achat seulement s'il est nul ou non renseigne
                if prix_achat > 0 and (not existing.prix_achat or existing.prix_achat == 0):
                    existing.prix_achat = prix_achat
                    changed = True
                # Met a jour la categorie si elle est absente
                if existing.categorie_id != cat.pk:
                    existing.categorie = cat
                    changed = True
                if changed:
                    existing.save()
                    self.stdout.write(f"  ~ {nom} (mis a jour)")
                    updated += 1
                else:
                    skipped += 1
            else:
                BoissonBar.objects.create(
                    nom=nom,
                    categorie=cat,
                    prix_achat=prix_achat,
                    prix=0,
                    unite_standard=unite,
                    disponible=True,
                    statut='actif',
                )
                self.stdout.write(f"  + {nom} ({prix_achat} F)")
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n{created} article(s) cree(s), {updated} mis a jour, {skipped} deja OK."
        ))
