from django.db import migrations


CHAMBRES = [
    # Suite Junior — 01, 02
    {'numero': '01', 'type_chambre': 'suite_junior', 'etage': 2, 'capacite': 3,
     'prix_nuit': 25000, 'prix_sejour': 50000, 'prix_nuitee': 50000},
    {'numero': '02', 'type_chambre': 'suite_junior', 'etage': 2, 'capacite': 3,
     'prix_nuit': 25000, 'prix_sejour': 50000, 'prix_nuitee': 50000},

    # Suite — 03, 04
    {'numero': '03', 'type_chambre': 'suite', 'etage': 2, 'capacite': 4,
     'prix_nuit': 30000, 'prix_sejour': 50000, 'prix_nuitee': 60000},
    {'numero': '04', 'type_chambre': 'suite', 'etage': 2, 'capacite': 4,
     'prix_nuit': 30000, 'prix_sejour': 50000, 'prix_nuitee': 60000},

    # Standard — 05 à 11
    {'numero': '05', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '06', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '07', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '08', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '09', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '10', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '11', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},

    # Supérieure — 12 à 18
    {'numero': '12', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '13', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '14', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '15', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '16', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '17', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},
    {'numero': '18', 'type_chambre': 'superieure', 'etage': 1, 'capacite': 2,
     'prix_nuit': 20000, 'prix_sejour': 40000, 'prix_nuitee': 45000},

    # Standard — 19, 20
    {'numero': '19', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
    {'numero': '20', 'type_chambre': 'standard', 'etage': 1, 'capacite': 2,
     'prix_nuit': 15000, 'prix_sejour': 30000, 'prix_nuitee': 35000},
]


def create_chambres(apps, schema_editor):
    Chambre = apps.get_model('hotel', 'Chambre')
    for data in CHAMBRES:
        Chambre.objects.get_or_create(
            numero=data['numero'],
            defaults={
                'type_chambre': data['type_chambre'],
                'etage':        data['etage'],
                'capacite':     data['capacite'],
                'prix_nuit':    data['prix_nuit'],
                'prix_sejour':  data['prix_sejour'],
                'prix_nuitee':  data['prix_nuitee'],
                'statut':       'disponible',
                'wifi':         True,
                'climatisation': True,
                'television':   True,
            }
        )


def delete_chambres(apps, schema_editor):
    Chambre = apps.get_model('hotel', 'Chambre')
    numeros = [c['numero'] for c in CHAMBRES]
    Chambre.objects.filter(numero__in=numeros).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0005_chambre_prix_repos_journee_suite_junior'),
    ]

    operations = [
        migrations.RunPython(create_chambres, delete_chambres),
    ]
