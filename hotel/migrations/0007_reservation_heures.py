from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0006_seed_chambres'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='heure_arrivee',
            field=models.TimeField(blank=True, null=True, verbose_name="Heure d'arrivée"),
        ),
        migrations.AddField(
            model_name='reservation',
            name='heure_depart',
            field=models.TimeField(blank=True, null=True, verbose_name='Heure de départ'),
        ),
    ]
