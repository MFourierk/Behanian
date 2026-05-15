import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0013_forfait_ligneforfait'),
        ('facturation', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SouscriptionForfait',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_client', models.CharField(blank=True, max_length=200, verbose_name="Nom client (saisie libre)")),
                ('date_souscription', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de souscription')),
                ('date_validite', models.DateField(blank=True, null=True, verbose_name="Valide jusqu'au")),
                ('statut', models.CharField(
                    choices=[('active', 'Active'), ('consommee', 'Consommée'), ('expiree', 'Expirée'), ('annulee', 'Annulée')],
                    default='active', max_length=15,
                )),
                ('montant_paye', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant payé (FCFA)')),
                ('mode_paiement', models.CharField(
                    choices=[
                        ('especes', 'Espèces'), ('mobile_money', 'Mobile Money'), ('orange_money', 'Orange Money'),
                        ('wave', 'Wave'), ('carte_bancaire', 'Carte Bancaire'), ('virement', 'Virement'),
                        ('cheque', 'Chèque'), ('autre', 'Autre'),
                    ],
                    default='especes', max_length=20,
                )),
                ('reference', models.CharField(blank=True, max_length=200, verbose_name='Référence (chambre, table, réservation…)')),
                ('notes', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='souscriptions_forfait',
                    to='facturation.client',
                    verbose_name='Client (compte)',
                )),
                ('cree_par', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='souscriptions_creees',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('forfait', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='souscriptions',
                    to='restaurant.forfait',
                    verbose_name='Forfait',
                )),
                ('ticket', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='souscription_forfait',
                    to='facturation.ticket',
                )),
            ],
            options={
                'verbose_name': 'Souscription forfait',
                'verbose_name_plural': 'Souscriptions forfait',
                'ordering': ['-date_souscription'],
            },
        ),
    ]
