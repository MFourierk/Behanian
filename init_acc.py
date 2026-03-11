
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from restaurant.models import CategorieMenu, PlatMenu

def init_accompagnements():
    # 1. Créer la catégorie Accompagnements
    cat, created = CategorieMenu.objects.get_or_create(
        nom="Accompagnements",
        defaults={'ordre': 99}
    )
    if created:
        print(f"Catégorie '{cat.nom}' créée.")
    else:
        print(f"Catégorie '{cat.nom}' existe déjà.")

    # 2. Créer quelques accompagnements
    accs = [
        {"nom": "Frites", "prix": 500},
        {"nom": "Alloco", "prix": 500},
        {"nom": "Riz blanc", "prix": 300},
        {"nom": "Attiéké", "prix": 300},
        {"nom": "Salade verte", "prix": 500},
    ]

    for item in accs:
        plat, p_created = PlatMenu.objects.get_or_create(
            nom=item["nom"],
            categorie=cat,
            defaults={
                'prix': item["prix"],
                'temps_preparation': 5,
                'disponible': True
            }
        )
        if p_created:
            print(f"Accompagnement '{plat.nom}' créé.")
        else:
            print(f"Accompagnement '{plat.nom}' existe déjà.")

if __name__ == '__main__':
    init_accompagnements()
