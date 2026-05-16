from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('piscine', '0005_add_reservation_hotel_field'),
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accespiscine',
            name='forfait',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='acces_piscine',
                to='restaurant.forfait',
                verbose_name='Forfait VIP souscrit',
            ),
        ),
        migrations.AddField(
            model_name='consommationpiscine',
            name='inclus_forfait',
            field=models.BooleanField(default=False, verbose_name='Inclus dans forfait VIP'),
        ),
    ]
