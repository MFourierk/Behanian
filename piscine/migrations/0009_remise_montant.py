from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piscine', '0008_acces_remise_pct'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accespiscine',
            name='remise_pct',
        ),
        migrations.AddField(
            model_name='accespiscine',
            name='remise_montant',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Remise (montant)'),
        ),
    ]
