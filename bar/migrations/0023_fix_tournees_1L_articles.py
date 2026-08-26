"""
Correctif migration 0022 :
- Jack Daniel, Baileys, Red Label : les tournées viennent des 700ml (pas des 1L)
  → ParametrageShot.volume_contenant_ml corrigé à 700
  → prix bouteille 700ml = 30 000 F (comme la carte)
- Création d'articles "1L" séparés (vente directe uniquement, sans ParametrageShot)
  → Jack Daniel 1L, Baileys 1L, Red Label 1L à 40 000 F chacun
"""
from decimal import Decimal
from django.db import migrations


CORRECTIONS = [
    # (mots-clés 700ml, nom article 1L, prix_bouteille_700, prix_1L)
    (['jack daniel'],  'Jack Daniel 1L',  30000, 40000),
    (['baileys'],      'Baileys 1L',      30000, 40000),
    (['red label'],    'Red Label 1L',    30000, 40000),
]


def _make_ref(BoissonBar, prefix):
    last = BoissonBar.objects.order_by('id').last()
    return f"{prefix[:3].upper()}-{(last.id + 1) if last else 1:04d}"


def corriger_et_creer_1L(apps, schema_editor):
    BoissonBar      = apps.get_model('bar', 'BoissonBar')
    ParametrageShot = apps.get_model('bar', 'ParametrageShot')

    for mots_cles, nom_1L, prix_700, prix_1L in CORRECTIONS:
        # Trouver la bouteille 700ml
        boisson_700 = None
        for mot in mots_cles:
            boisson_700 = BoissonBar.objects.filter(
                nom__icontains=mot,
                statut='actif',
                est_shot=False,
            ).exclude(nom__icontains='1L').first()
            if boisson_700:
                break

        if not boisson_700:
            print(f"  ⚠️  Article 700ml introuvable pour : {mots_cles}")
            continue

        # Corriger le ParametrageShot → volume 700ml
        updated = ParametrageShot.objects.filter(boisson=boisson_700).update(
            volume_contenant_ml=700
        )
        # Corriger le prix de la bouteille 700ml
        BoissonBar.objects.filter(pk=boisson_700.pk).update(prix=Decimal(str(prix_700)))

        if updated:
            print(f"  ✓  {boisson_700.nom} → volume corrigé à 700ml, prix={prix_700}F")
        else:
            print(f"  ⚠️  Pas de ParametrageShot trouvé pour {boisson_700.nom}")

        # Créer l'article 1L si absent
        if not BoissonBar.objects.filter(nom__iexact=nom_1L).exists():
            BoissonBar.objects.create(
                nom=nom_1L,
                categorie=boisson_700.categorie,
                prix=Decimal(str(prix_1L)),
                prix_achat=Decimal('0'),
                unite_standard='bouteille',
                quantite_stock=0,
                seuil_alerte=2,
                disponible=True,
                statut='actif',
                est_shot=False,
                reference=_make_ref(BoissonBar, nom_1L),
            )
            print(f"  ✓  Article créé : {nom_1L} à {prix_1L}F")
        else:
            print(f"  —  Article déjà existant : {nom_1L}")


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0022_parametrage_shots_liqueurs'),
    ]

    operations = [
        migrations.RunPython(corriger_et_creer_1L, migrations.RunPython.noop),
    ]
