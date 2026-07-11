# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from restaurant.models import CategorieMenu, PlatMenu


ENTREES = [
    ("Plateau d’entrée",       15000),
    ("Plateau d’entrée Grand", 20000),
    ("Œuf au plat nature",           3000),
    ("Salade Mixte",                      3000),
    ("Salade Fermier",                    5000),
    ("Salade Behanian",                   5000),
    ("Tomate farcie",                     5000),
]

DESSERTS = [
    ("Salade de fruit",    2500),
    ("Brochette de fruit", 2500),
    ("Yaourt",             2500),
    ("Crêpe",         2500),
    ("Glace",              1500),
]


class Command(BaseCommand):
    help = "Initialise les entrées et desserts comme plats simples (sans stock)"

    def handle(self, *args, **options):
        cat_entree, _ = CategorieMenu.objects.get_or_create(
            nom="Hors-d’œuvre / Entrée",
            defaults={"ordre": 1}
        )
        cat_dessert, _ = CategorieMenu.objects.get_or_create(
            nom="Desserts",
            defaults={"ordre": 5}
        )

        created_total = 0
        for nom, prix in ENTREES:
            _, created = PlatMenu.objects.get_or_create(
                nom=nom, categorie=cat_entree,
                defaults={"prix": prix, "is_simple": True, "disponible": True, "temps_preparation": 0}
            )
            if created:
                created_total += 1
                self.stdout.write(f"  + {nom} ({prix} F)")

        for nom, prix in DESSERTS:
            _, created = PlatMenu.objects.get_or_create(
                nom=nom, categorie=cat_dessert,
                defaults={"prix": prix, "is_simple": True, "disponible": True, "temps_preparation": 0}
            )
            if created:
                created_total += 1
                self.stdout.write(f"  + {nom} ({prix} F)")

        self.stdout.write(self.style.SUCCESS(
            f"{created_total} article(s) créé(s). Entrées et desserts disponibles au restaurant."
        ))
