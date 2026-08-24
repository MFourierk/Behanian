# Generated manually — ajoute VenteCave / LigneVenteCave (traçabilité vente Cave)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0016_fix_shot_articles_est_shot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VenteCave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_vente', models.DateTimeField(auto_now_add=True)),
                ('espace', models.CharField(blank=True, default='', max_length=50)),
                ('reference', models.CharField(blank=True, default='', max_length=100)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('serveur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ventes_cave_servies', to=settings.AUTH_USER_MODEL)),
                ('utilisateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ventes_cave_encaissees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vente Cave',
                'verbose_name_plural': 'Ventes Cave',
                'ordering': ['-date_vente'],
            },
        ),
        migrations.CreateModel(
            name='LigneVenteCave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_article', models.CharField(blank=True, default='', max_length=200)),
                ('quantite', models.IntegerField(default=1)),
                ('prix_unitaire', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('boisson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bar.boissonbar')),
                ('vente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='bar.ventecave')),
            ],
            options={
                'verbose_name': 'Ligne de vente (Cave)',
                'verbose_name_plural': 'Lignes de vente (Cave)',
            },
        ),
    ]
