from django.db import migrations, models
import django.db.models.deletion


def marquer_lignes_existantes(apps, schema_editor):
    LigneInventaireBar = apps.get_model('bar', 'LigneInventaireBar')
    LigneInventaireBar.objects.all().update(statut='compte')


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0026_alter_boissonbar_marge_alter_boissonbar_prix_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventairebar',
            name='type_inventaire',
            field=models.CharField(choices=[('complet', 'Inventaire complet'), ('partiel', 'Inventaire partiel'), ('correction', 'Correction')], default='complet', max_length=20, verbose_name='Type'),
        ),
        migrations.AddField(
            model_name='inventairebar',
            name='inventaire_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corrections', to='bar.inventairebar', verbose_name='Inventaire source (correction)'),
        ),
        migrations.AddField(
            model_name='ligneinventairebar',
            name='statut',
            field=models.CharField(choices=[('a_compter', 'À compter'), ('compte', 'Compté'), ('confirme_zero', 'Confirmé à zéro')], default='a_compter', max_length=20, verbose_name='Statut'),
        ),
        migrations.AlterField(
            model_name='ligneinventairebar',
            name='quantite_comptee',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name='Qté comptée (physique)'),
        ),
        migrations.RunPython(marquer_lignes_existantes, migrations.RunPython.noop),
    ]
