from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0001_initial'),
        ('piscine', '0003_alter_accespiscine_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='accespiscine',
            name='nb_adultes',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='accespiscine',
            name='nb_enfants',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='accespiscine',
            name='reservation_hotel',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='acces_piscine',
                to='hotel.reservation',
                verbose_name='Reservation hotel liee'
            ),
        ),
    ]
