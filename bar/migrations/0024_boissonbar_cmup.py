from django.db import migrations, models


def initialiser_cmup(apps, schema_editor):
    """Initialise le CMUP au prix_achat actuel pour tous les articles existants."""
    BoissonBar = apps.get_model('bar', 'BoissonBar')
    BoissonBar.objects.filter(cmup=0).update(cmup=models.F('prix_achat'))


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0023_fix_tournees_1L_articles'),
    ]

    operations = [
        migrations.AddField(
            model_name='boissonbar',
            name='cmup',
            field=models.DecimalField(
                decimal_places=4, default=0, max_digits=10,
                verbose_name='CMUP (Coût Moyen Unitaire Pondéré)'
            ),
        ),
        migrations.RunPython(initialiser_cmup, migrations.RunPython.noop),
    ]
