"""
Migration 0028 : Architecture pro pour les bouteilles ouvertes.

Avant : quantite_stock incluait les bouteilles ouvertes ; ml_en_cours = ml consommés.
Après : quantite_stock = bouteilles SCELLÉES seulement ; ml_ouverts = ml disponibles
        dans les bouteilles en cours d'utilisation.

Conversion des données existantes :
  - Si ml_en_cours > 0 : la bouteille ouverte quitte quantite_stock et son
    ml restant (volume - ml_en_cours) est transféré dans ml_ouverts.
  - ml_en_cours est remis à 0 (champ conservé mais obsolète).

Nouveau type de mouvement 'ouverture_contenant' (neutre, pas d'impact stock)
pour tracer chaque ouverture de bouteille entamée.
"""
from django.db import migrations, models
from decimal import Decimal


def migrer_ml_ouverts(apps, schema_editor):
    """Convertit ml_en_cours (consommés) → ml_ouverts (restants) et ajuste quantite_stock."""
    ParametrageShot = apps.get_model('bar', 'ParametrageShot')
    BoissonBar = apps.get_model('bar', 'BoissonBar')

    for param in ParametrageShot.objects.select_related('boisson').all():
        if param.ml_en_cours and param.ml_en_cours > 0:
            ml_restants = max(Decimal('0'), param.volume_contenant_ml - param.ml_en_cours)
            param.ml_ouverts = ml_restants
            # La bouteille ouverte sort du stock scellé
            boisson = param.boisson
            if boisson.quantite_stock > 0:
                boisson.quantite_stock = max(0, boisson.quantite_stock - 1)
                boisson.save(update_fields=['quantite_stock'])
            param.ml_en_cours = Decimal('0')
        else:
            param.ml_ouverts = Decimal('0')
        param.save(update_fields=['ml_ouverts', 'ml_en_cours'])


def rollback_ml_ouverts(apps, schema_editor):
    """Rollback : reconvertit ml_ouverts → ml_en_cours et restaure quantite_stock."""
    ParametrageShot = apps.get_model('bar', 'ParametrageShot')
    BoissonBar = apps.get_model('bar', 'BoissonBar')

    for param in ParametrageShot.objects.select_related('boisson').all():
        if param.ml_ouverts and param.ml_ouverts > 0:
            ml_en_cours = max(Decimal('0'), param.volume_contenant_ml - param.ml_ouverts)
            param.ml_en_cours = ml_en_cours
            boisson = param.boisson
            boisson.quantite_stock += 1
            boisson.save(update_fields=['quantite_stock'])
            param.ml_ouverts = Decimal('0')
        param.save(update_fields=['ml_ouverts', 'ml_en_cours'])


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0027_inventairebar_type_source_ligneinventairebar_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametrageshot',
            name='ml_ouverts',
            field=models.DecimalField(
                decimal_places=3, default=0, max_digits=10,
                verbose_name='ml disponibles (bouteilles ouvertes)',
                help_text='Total des ml restants dans toutes les bouteilles en cours d\'utilisation'
            ),
        ),
        migrations.AlterField(
            model_name='parametrageshot',
            name='ml_en_cours',
            field=models.DecimalField(
                decimal_places=3, default=0, max_digits=10,
                verbose_name='ml consommés (OBSOLÈTE — ne pas utiliser)'
            ),
        ),
        migrations.AlterField(
            model_name='mouvementstockbar',
            name='type_mouvement',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('entree',               'Entrée (Achat/Réception)'),
                    ('sortie',               'Sortie (Vente)'),
                    ('casse',                'Casse / Perte'),
                    ('inventaire_excedent',  'Inventaire — Excédent'),
                    ('inventaire_manquant',  'Inventaire — Manquant'),
                    ('inventaire',           'Inventaire — Conforme'),
                    ('ouverture_contenant',  'Ouverture contenant (bouteille entamée)'),
                ]
            ),
        ),
        migrations.RunPython(migrer_ml_ouverts, rollback_ml_ouverts),
    ]
