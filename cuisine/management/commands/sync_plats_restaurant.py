from django.core.management.base import BaseCommand
from cuisine.models import Plat
from restaurant.models import PlatMenu, CategorieMenu


class Command(BaseCommand):
    help = "Synchronise tous les plats Cuisine vers Restaurant"

    def handle(self, *args, **kwargs):

        plats_actifs = Plat.objects.exclude(statut='archive').select_related('categorie')
        ids_cuisine  = set(p.pk for p in plats_actifs)
        self.stdout.write(f"Plats cuisine actifs : {plats_actifs.count()}\n")

        # ── Étape 1 : établir les liens cuisine_plat_id manquants ─────────
        for plat in plats_actifs:
            pm = PlatMenu.objects.filter(nom__iexact=plat.nom,
                                         cuisine_plat_id__isnull=True).first()
            if pm:
                pm.cuisine_plat_id = plat.pk
                pm.save(update_fields=['cuisine_plat_id'])
                self.stdout.write(f"  Lien établi : {plat.nom} → ID {plat.pk}")

        # ── Étape 2 : synchro complète ────────────────────────────────────
        for plat in plats_actifs:
            cat_nom   = plat.categorie.nom if plat.categorie else 'Plats'
            cat, _    = CategorieMenu.objects.get_or_create(
                            nom=cat_nom, defaults={'ordre': 1})

            # Chercher par ID cuisine en priorité, puis par nom
            pm = PlatMenu.objects.filter(cuisine_plat_id=plat.pk).first()
            if not pm:
                pm = PlatMenu.objects.filter(nom__iexact=plat.nom).first()

            if pm:
                pm.nom             = plat.nom
                pm.cuisine_plat_id = plat.pk
                pm.categorie       = cat
                pm.prix            = plat.prix_vente
                pm.disponible      = (plat.statut == 'disponible')
                pm.description     = plat.description_carte or ''
                pm.save()
                self.stdout.write(f"  ✓ Mis à jour : {plat.nom}")
            else:
                PlatMenu.objects.create(
                    cuisine_plat_id  = plat.pk,
                    nom              = plat.nom,
                    categorie        = cat,
                    prix             = plat.prix_vente,
                    temps_preparation= 15,
                    disponible       = (plat.statut == 'disponible'),
                    description      = plat.description_carte or '',
                )
                self.stdout.write(f"  + Créé : {plat.nom}")

        # ── Étape 3 : supprimer les orphelins ─────────────────────────────
        noms_cuisine = set(p.nom.lower().strip() for p in plats_actifs)
        for pm in PlatMenu.objects.all():
            if pm.cuisine_plat_id:
                if pm.cuisine_plat_id not in ids_cuisine:
                    self.stdout.write(f"  ✗ Supprimé (ID inconnu) : {pm.nom}")
                    pm.delete()
            else:
                if pm.nom.lower().strip() not in noms_cuisine:
                    self.stdout.write(f"  ✗ Supprimé (orphelin) : {pm.nom}")
                    pm.delete()

        # ── Résultat ──────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Cuisine : {plats_actifs.count()} plats"
            f"  |  Restaurant : {PlatMenu.objects.count()} plats"
        ))
