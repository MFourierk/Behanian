from django.db import migrations, models


def marquer_salons_prives(apps, schema_editor):
    Table = apps.get_model('restaurant', 'Table')
    Table.objects.filter(numero__startswith='SAPR').update(est_salon_prive=True, tarif_horaire=5000)
    Table.objects.filter(numero__startswith='SSPRI').update(est_salon_prive=True, tarif_horaire=5000)


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0022_add_platmenu_carpe_fix_stpierre_petit'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='est_salon_prive',
            field=models.BooleanField(default=False, verbose_name='Salon privé'),
        ),
        migrations.AddField(
            model_name='table',
            name='tarif_horaire',
            field=models.DecimalField(decimal_places=2, default=5000, max_digits=10, verbose_name='Tarif horaire (F)'),
        ),
        migrations.RunPython(marquer_salons_prives, migrations.RunPython.noop),
    ]
