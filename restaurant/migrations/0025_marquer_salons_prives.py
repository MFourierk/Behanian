from django.db import migrations


def marquer_salons_prives(apps, schema_editor):
    """Rattraper les tables SAPR/SSPRI créées après la migration 0023."""
    Table = apps.get_model('restaurant', 'Table')
    Table.objects.filter(
        numero__icontains='SAPR', est_salon_prive=False
    ).update(est_salon_prive=True, tarif_horaire=5000)
    Table.objects.filter(
        numero__icontains='SSPRI', est_salon_prive=False
    ).update(est_salon_prive=True, tarif_horaire=5000)


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0024_alter_commande_montant_rendu_and_more'),
    ]

    operations = [
        migrations.RunPython(marquer_salons_prives, migrations.RunPython.noop),
    ]
