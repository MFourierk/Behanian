"""
Migration 0005 : Ajout des champs journaliers à CaisseSession
- date_session     : date explicite de la session
- numero_session   : identifiant séquentiel lisible
- solde_theorique  : solde calculé théorique à la clôture
- ecart            : différence solde_theorique − fond_caisse_reel
"""
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0004_alter_caissesession_type_caisse'),
    ]

    operations = [
        migrations.AddField(
            model_name='caissesession',
            name='date_session',
            field=models.DateField(default=django.utils.timezone.localdate,
                                   help_text='Date de la session (YYYY-MM-DD)'),
        ),
        migrations.AddField(
            model_name='caissesession',
            name='numero_session',
            field=models.CharField(blank=True, max_length=30,
                                   help_text='Identifiant séquentiel ex: SES-20260410-HOT-001'),
        ),
        migrations.AddField(
            model_name='caissesession',
            name='solde_theorique',
            field=models.DecimalField(decimal_places=2, default=0,
                                      help_text='Fond initial + espèces encaissées − prélèvements banque',
                                      max_digits=12),
        ),
        migrations.AddField(
            model_name='caissesession',
            name='ecart',
            field=models.DecimalField(decimal_places=2, default=0,
                                      help_text='Écart = Solde théorique − Fond réel compté (négatif = manquant)',
                                      max_digits=12),
        ),
        migrations.AlterModelOptions(
            name='caissesession',
            options={
                'ordering': ['-opened_at'],
                'verbose_name': 'Session de caisse',
                'verbose_name_plural': 'Sessions de caisse',
            },
        ),
    ]
