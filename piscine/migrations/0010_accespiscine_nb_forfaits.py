from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piscine', '0009_remise_montant'),
    ]

    operations = [
        migrations.AddField(
            model_name='accespiscine',
            name='nb_forfaits',
            field=models.IntegerField(default=1, verbose_name='Nombre de menus VIP'),
        ),
    ]
