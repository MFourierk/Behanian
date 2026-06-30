import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0003_serveur_consommation'),
        ('piscine', '0007_serveur_consommation'),
    ]

    operations = [
        # Chambre: prix_nuit et prix_sejour → DecimalField
        migrations.AlterField(
            model_name='chambre',
            name='prix_nuit',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix Nuitée (FCFA)'),
        ),
        migrations.AlterField(
            model_name='chambre',
            name='prix_sejour',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Prix Séjour (FCFA)'),
        ),
        # Reservation: prix_total et avance → DecimalField
        migrations.AlterField(
            model_name='reservation',
            name='prix_total',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix total (FCFA)'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='avance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Avance payée (FCFA)'),
        ),
        # Consommation: FK vers AccesPiscine
        migrations.AddField(
            model_name='consommation',
            name='acces_piscine',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='piscine.accespiscine',
            ),
        ),
    ]
