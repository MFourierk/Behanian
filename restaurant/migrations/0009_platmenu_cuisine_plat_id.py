# Migration vide — placeholder pour aligner les numéros entre les deux branches.
# Sur la branche principale (serveur) : 0008=forfait, 0009=placeholder, 0010=cuisine_plat_id
# Sur la branche utilisateur          : 0008=forfait, 0009=remove_ligneforfait, 0010=cuisine_plat_id
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0008_forfait_ligneforfait'),
    ]

    operations = []
