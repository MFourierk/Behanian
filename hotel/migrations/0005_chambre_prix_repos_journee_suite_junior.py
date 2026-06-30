from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0004_decimal_prices_piscine_fk'),
    ]

    operations = [
        # Nouveau type suite_junior
        migrations.AlterField(
            model_name='chambre',
            name='type_chambre',
            field=models.CharField(
                choices=[
                    ('standard', 'Standard'),
                    ('superieure', 'Supérieure'),
                    ('suite_junior', 'Suite Junior'),
                    ('suite', 'Suite'),
                    ('vip', 'VIP'),
                ],
                max_length=20,
                verbose_name='Type',
            ),
        ),
        # Renommer verbose_name de prix_nuit → Repos 4h
        migrations.AlterField(
            model_name='chambre',
            name='prix_nuit',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix Repos 4h (FCFA)'),
        ),
        # Renommer verbose_name de prix_sejour → Journée 10h
        migrations.AlterField(
            model_name='chambre',
            name='prix_sejour',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Prix Journée 10h (FCFA)'),
        ),
        # Nouveau champ Nuitée 24h
        migrations.AddField(
            model_name='chambre',
            name='prix_nuitee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Prix Nuitée 24h (FCFA)'),
        ),
        # Nouveaux choix type_sejour sur Reservation
        migrations.AlterField(
            model_name='reservation',
            name='type_sejour',
            field=models.CharField(
                choices=[
                    ('repos', 'Repos (4h)'),
                    ('journee', 'Journée (10h)'),
                    ('nuitee', 'Nuitée (24h)'),
                    ('long_sejour', 'Long Séjour'),
                ],
                default='nuitee',
                max_length=20,
                verbose_name='Type de Séjour',
            ),
        ),
    ]
