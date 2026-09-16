from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0015_alter_ticket_mode_paiement'),
    ]

    operations = [
        migrations.CreateModel(
            name='LignePaiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode_paiement', models.CharField(choices=[
                    ('especes',       'Espèces'),
                    ('wave',          'Wave'),
                    ('orange_money',  'Orange Money'),
                    ('mtn_money',     'MTN Mobile Money'),
                    ('moov_money',    'Moov Money'),
                    ('mobile_money',  'Mobile Money'),
                    ('carte_bancaire','Carte Bancaire'),
                    ('cheque',        'Chèque'),
                    ('virement',      'Virement'),
                    ('autre',         'Autre'),
                ], max_length=30)),
                ('montant', models.DecimalField(decimal_places=3, max_digits=10)),
                ('ticket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lignes_paiement',
                    to='facturation.ticket',
                )),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
