from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piscine', '0007_serveur_consommation'),
    ]

    operations = [
        migrations.AddField(
            model_name='accespiscine',
            name='remise_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Remise (%)'),
        ),
    ]
