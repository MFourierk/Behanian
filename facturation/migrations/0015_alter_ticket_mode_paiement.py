# Generated manually - ajout du choix 'mixte' au mode_paiement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0014_ticket_montant_especes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='mode_paiement',
            field=models.CharField(
                choices=[
                    ('especes', 'Espèces'),
                    ('mixte', 'Mixte'),
                    ('mobile_money', 'Mobile Money'),
                    ('orange_money', 'Orange Money'),
                    ('wave', 'Wave'),
                    ('moov_money', 'Moov Money'),
                    ('mtn_money', 'MTN Mobile Money'),
                    ('carte_bancaire', 'Carte Bancaire'),
                    ('carte', 'Carte Bancaire'),
                    ('cheque', 'Chèque'),
                    ('virement', 'Virement'),
                    ('cave', 'Cave'),
                    ('autre', 'Autre'),
                ],
                default='especes',
                max_length=50,
            ),
        ),
    ]
