"""
Commande : python manage.py sync_plats_restaurant
Migration one-shot + synchro complète Cuisine → Restaurant.
Établit les liens cuisine_plat_id manquants et nettoie les orphelins.
"""
from django.core.management.base import BaseCommand
from cuisine.models import Plat
from restaurant.models import PlatMenu, CategorieMenu


class Command(BaseCommand):
    help = "Synchronise tous les plats Cuisine → Restaurant (migration cuisine_plat_id)"

    def handle(self, *args, **kwargs):
        self.stdout.write("=== Synchronisation Cuisine → Restaurant ===\n")

        plats_cuisine = Plat.objects.exclude(statut='archive').select_related('categorie')
        self.stdout.write(f"Plats cuisine actifs : {plats_cuisine.count()}")

        # Étape 1 : Établir les liens cuisine_plat_id manquants
        liens_etablis = 0
        for plat in plats_cuisine:
            # Chercher le PlatMenu correspondant sans lien
            pm = PlatMenu.objects.filter(cuisine_plat_id=plat.pk).first()
            if not pm:
                # Chercher par nom exact
                pm = PlatMenu.objects.filter(nom__iexact=plat.nom).first()
                if pm and not pm.cuisine_plat_id:
                    pm.cuisine_plat_id = plat.pk
                    pm.save(update_fields=['cuisine_plat_id'])
                    self.stdout.write(f"  Lien établi: {plat.nom} (cuisine ID={plat.pk})")
                    liens_etablis += 1

        self.stdout.write(f"\nLiens établis : {liens_etablis}")

        # Étape 2 : Synchro complète (crée ou met à jour)
        from cuisine.views import _sync_plat_to_restaurant
        syncronises = 0
        for plat in plats_cuisine:
            _sync_plat_to_restaurant(plat)
            syncronises += 1
            self.stdout.write(f"  ✓ {plat.nom}")

        self.stdout.write(f"\nSynchronisés : {syncronises}")

        # Étape 3 : Épuration des orphelins
        from cuisine.views import _epurer_plats_restaurant
        supprimes = _epurer_plats_restaurant()
        if supprimes:
            self.stdout.write(f"\nOrphelins supprimés ({len(supprimes)}) :")
            for nom in supprimes:
                self.stdout.write(f"  ✗ {nom}")
        else:
            self.stdout.write("\nAucun orphelin.")

        # Résumé final
        self.stdout.write("\n=== Résultat final ===")
        self.stdout.write(f"Plats en Cuisine : {plats_cuisine.count()}")
        self.stdout.write(f"Plats au Restaurant : {PlatMenu.objects.count()}")
        self.stdout.write(self.style.SUCCESS("\n✅ Synchronisation terminée !"))
