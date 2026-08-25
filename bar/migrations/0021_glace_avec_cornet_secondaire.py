from django.db import migrations


def link_cornet(apps, schema_editor):
    BoissonBar = apps.get_model('bar', 'BoissonBar')
    try:
        glace_ac = BoissonBar.objects.get(reference='GLA-AC')
        cornet   = BoissonBar.objects.get(reference='GLA-COR')
        glace_ac.ingredient_secondaire = cornet
        glace_ac.quantite_secondaire   = 1
        glace_ac.save()
    except BoissonBar.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0020_boisson_ingredient_secondaire'),
    ]

    operations = [
        migrations.RunPython(link_cornet, migrations.RunPython.noop),
    ]
