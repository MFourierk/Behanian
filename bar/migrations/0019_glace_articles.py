from decimal import Decimal
from django.db import migrations


PRIX_BAC       = Decimal('13000')
BOULES_PAR_BAC = 35
PRIX_BOULE     = (PRIX_BAC / BOULES_PAR_BAC).quantize(Decimal('0.01'))  # 371.43 F
PRIX_CORNET    = Decimal('120')    # 3000 / 25
PRIX_VENTE     = Decimal('1500')


def create_glace(apps, schema_editor):
    CategorieBar      = apps.get_model('bar', 'CategorieBar')
    UniteVente        = apps.get_model('bar', 'UniteVente')
    BoissonBar        = apps.get_model('bar', 'BoissonBar')
    ParametrageShot   = apps.get_model('bar', 'ParametrageShot')

    # ── Catégorie ──────────────────────────────────────────────────────
    cat, _ = CategorieBar.objects.get_or_create(
        nom='Glace & Desserts',
        defaults={'ordre': 10},
    )

    # ── Unités ─────────────────────────────────────────────────────────
    unite_bac, _    = UniteVente.objects.get_or_create(nom='Bac',    defaults={'abreviation': 'bac'})
    unite_cornet, _ = UniteVente.objects.get_or_create(nom='Cornet', defaults={'abreviation': 'cornet'})

    # ── Article parent : Bac de glace (stock en bacs) ──────────────────
    if not BoissonBar.objects.filter(reference='GLA-BAC').exists():
        bac = BoissonBar.objects.create(
            reference='GLA-BAC',
            nom='Bac de glace',
            categorie=cat,
            prix_achat=PRIX_BAC,
            prix=0,
            mode_prix='manuel',
            unite_standard='autre',
            unite_personnalisee=unite_bac,
            quantite_stock=100,
            seuil_alerte=2,
            disponible=False,       # vendu uniquement via les FT dérivées
            statut='actif',
        )
    else:
        bac = BoissonBar.objects.get(reference='GLA-BAC')

    # ── Article stock : Cornet de glace ───────────────────────────────
    if not BoissonBar.objects.filter(reference='GLA-COR').exists():
        BoissonBar.objects.create(
            reference='GLA-COR',
            nom='Cornet de glace',
            categorie=cat,
            prix_achat=PRIX_CORNET,
            prix=0,
            mode_prix='manuel',
            unite_standard='autre',
            unite_personnalisee=unite_cornet,
            quantite_stock=100,
            seuil_alerte=10,
            disponible=False,       # comptabilisé lors de la vente glace-cornet
            statut='actif',
        )

    # ── FT glace sans cornet (2 boules) ───────────────────────────────
    if not BoissonBar.objects.filter(reference='GLA-SC').exists():
        BoissonBar.objects.create(
            reference='GLA-SC',
            nom='Glace sans cornet',
            categorie=cat,
            prix_achat=PRIX_BOULE * 2,
            prix=PRIX_VENTE,
            mode_prix='manuel',
            unite_standard='verre',
            quantite_stock=0,
            seuil_alerte=0,
            disponible=True,
            statut='actif',
            est_shot=True,
            shot_ml=2,          # 2 boules par service
            shot_parent=bac,
        )

    # ── FT glace avec cornet (1 cornet + 2 boules) ────────────────────
    if not BoissonBar.objects.filter(reference='GLA-AC').exists():
        BoissonBar.objects.create(
            reference='GLA-AC',
            nom='Glace avec cornet',
            categorie=cat,
            prix_achat=PRIX_BOULE * 2 + PRIX_CORNET,
            prix=PRIX_VENTE,
            mode_prix='manuel',
            unite_standard='verre',
            quantite_stock=0,
            seuil_alerte=0,
            disponible=True,
            statut='actif',
            est_shot=True,
            shot_ml=2,          # 2 boules par service
            shot_parent=bac,
        )

    # ── ParametrageShot pour Bac de glace ─────────────────────────────
    # volume_contenant_ml=35 : 1 bac = 35 boules
    # volume_shot_ml=2       : 1 service = 2 boules
    # article_shot/tournee=None : on n'utilise pas les articles auto-générés
    if not ParametrageShot.objects.filter(boisson=bac).exists():
        ParametrageShot.objects.create(
            boisson=bac,
            volume_contenant_ml=35,
            volume_shot_ml=2,
            prix_shot=PRIX_VENTE,
            prix_tournee=PRIX_VENTE,
            ml_en_cours=0,
            actif=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0018_stock_100_all_boissons'),
    ]

    operations = [
        migrations.RunPython(create_glace, migrations.RunPython.noop),
    ]
