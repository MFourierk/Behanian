"""
Crée les ParametrageShot + articles virtuels Shot/Tournée pour toutes les liqueurs.
- 1 tournée = 2 shots × 30 ml = 60 ml
- Bouteilles 1L (Baileys, Red Label, Jack Daniel) : volume_contenant = 1 000 ml, prix bouteille = 40 000 F
- Toutes les autres : 700 ml, prix bouteille depuis la carte
- Prix shot = prix tournée / 2
"""
from decimal import Decimal
from django.db import migrations


# (mots-clés de recherche, volume_ml, prix_tournee, prix_bouteille)
LIQUEURS = [
    (['jack daniel'],               1000, 3000, 40000),
    (['baileys'],                   1000, 2000, 40000),
    (['red label'],                 1000, 2500, 40000),
    (['black label'],                700, 3000, 40000),
    (['campari'],                    700, 2000, 15000),
    (['chivas'],                     700, 3000, 45000),
    (['clan camp', 'clan camb'],     700, 2500, 35000),
    (['cointreau'],                  700, 3000, 45000),
    (['gordon'],                     700, 2500, 25000),
    (['j.b', 'jb whisky', 'j.b.'],  700, 2500, 15000),
    (['mangoustan', 'mangoustin'],   700, 2500, 25000),
    (['martini'],                    700, 2000, 15000),
    (['pastis 51', 'pastis51'],      700, 2000, 15000),
    (['ricard'],                     700, 2000, 15000),
    (['st james', 'saint james'],    700, 2500, 25000),
    (['whisky p'],                   700, 2500, 15000),  # Whisky Pêche / Peche
]


def _trouver_boisson(BoissonBar, mots_cles):
    for mot in mots_cles:
        art = BoissonBar.objects.filter(
            nom__icontains=mot,
            statut='actif',
            est_shot=False,
        ).first()
        if art:
            return art
    return None


def _make_ref(BoissonBar, prefix):
    last = BoissonBar.objects.order_by('id').last()
    return f"{prefix}-{(last.id + 1) if last else 1:04d}"


def creer_parametrages(apps, schema_editor):
    BoissonBar      = apps.get_model('bar', 'BoissonBar')
    ParametrageShot = apps.get_model('bar', 'ParametrageShot')

    for mots_cles, volume_ml, prix_tournee, prix_bouteille in LIQUEURS:
        boisson = _trouver_boisson(BoissonBar, mots_cles)
        if not boisson:
            print(f"  ⚠️  Liqueur introuvable : {mots_cles}")
            continue

        prix_tournee_d   = Decimal(str(prix_tournee))
        prix_shot_d      = prix_tournee_d / 2
        prix_bouteille_d = Decimal(str(prix_bouteille))

        # Mise à jour prix bouteille
        if boisson.prix != prix_bouteille_d:
            BoissonBar.objects.filter(pk=boisson.pk).update(prix=prix_bouteille_d)

        # Récupérer ou créer le ParametrageShot (sans save() custom)
        param, created = ParametrageShot.objects.get_or_create(
            boisson=boisson,
            defaults={
                'volume_contenant_ml': volume_ml,
                'volume_shot_ml':      30,
                'prix_shot':           prix_shot_d,
                'prix_tournee':        prix_tournee_d,
                'actif':               True,
            },
        )
        if not created:
            ParametrageShot.objects.filter(pk=param.pk).update(
                volume_contenant_ml=volume_ml,
                volume_shot_ml=30,
                prix_shot=prix_shot_d,
                prix_tournee=prix_tournee_d,
                actif=True,
            )
            param = ParametrageShot.objects.get(pk=param.pk)

        # ----- Créer / mettre à jour les articles virtuels Shot et Tournée -----
        nom_shot    = f"{boisson.nom} — Shot"
        nom_tournee = f"{boisson.nom} — Tournée"

        def _upsert_virtuel(art_existant, nom, shot_ml, prix):
            if art_existant:
                BoissonBar.objects.filter(pk=art_existant.pk).update(
                    nom=nom, prix=prix, shot_ml=shot_ml,
                    est_shot=True, shot_parent=boisson,
                    disponible=True, statut='actif',
                )
                return art_existant
            else:
                return BoissonBar.objects.create(
                    nom=nom,
                    categorie=boisson.categorie,
                    prix=prix,
                    unite_standard='verre',
                    quantite_stock=0,
                    seuil_alerte=0,
                    disponible=True,
                    statut='actif',
                    est_shot=True,
                    shot_ml=shot_ml,
                    shot_parent=boisson,
                    reference=_make_ref(BoissonBar, nom[:3].upper()),
                )

        art_shot    = _upsert_virtuel(param.article_shot,    nom_shot,    30, prix_shot_d)
        art_tournee = _upsert_virtuel(param.article_tournee, nom_tournee, 60, prix_tournee_d)

        # Lier les articles au ParametrageShot
        ParametrageShot.objects.filter(pk=param.pk).update(
            article_shot=art_shot,
            article_tournee=art_tournee,
        )

        action = 'créé' if created else 'mis à jour'
        print(f"  ✓  {boisson.nom} ({volume_ml}ml) — {action} | Shot={prix_shot_d}F | Tournée={prix_tournee_d}F | Bouteille={prix_bouteille_d}F")


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0021_glace_avec_cornet_secondaire'),
    ]

    operations = [
        migrations.RunPython(creer_parametrages, migrations.RunPython.noop),
    ]
