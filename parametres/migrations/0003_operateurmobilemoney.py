from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0002_auto_20260218_2014'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperateurMobileMoney',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name="Nom de l'opérateur")),
                ('image', models.ImageField(blank=True, null=True, upload_to='mobile_money/', verbose_name='Logo')),
                ('ordre', models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
            ],
            options={
                'verbose_name': 'Opérateur Mobile Money',
                'verbose_name_plural': 'Opérateurs Mobile Money',
                'ordering': ['ordre', 'nom'],
            },
        ),
    ]
