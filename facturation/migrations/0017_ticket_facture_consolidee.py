from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0016_lignepaiement'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='facture_consolidee',
            field=models.ForeignKey(
                blank=True,
                help_text='Facture globale regroupant ce ticket (exclut du CA caisse)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tickets_consolides',
                to='facturation.facture',
            ),
        ),
    ]
