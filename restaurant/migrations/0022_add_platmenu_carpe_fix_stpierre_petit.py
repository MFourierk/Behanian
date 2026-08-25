from django.db import migrations


CAT_POISSONS = 10
TEMPS_PREP = 15


def add_carpe_fix_stpierre(apps, schema_editor):
    PlatMenu = apps.get_model('restaurant', 'PlatMenu')
    Plat = apps.get_model('cuisine', 'Plat')

    # ----------------------------------------------------------------
    # St Pierre Petit — 9 000 → 10 000
    # ----------------------------------------------------------------
    for cuisson in ['Braisé', 'Soupe', 'Sauté', 'Frit']:
        PlatMenu.objects.filter(nom__iexact=f'St Pierre {cuisson} Petit', prix=9000).update(prix=10000)

    # ----------------------------------------------------------------
    # Carpe — créer PlatMenu (Petit 10 000, Moyen 12 000, Grand 15 000)
    # ----------------------------------------------------------------
    for cuisson in ['Braisée', 'Frit', 'Sautée', 'Soupe']:
        for taille, prix in [('Petit', 10000), ('Moyen', 12000), ('Grand', 15000)]:
            nom = f'Carpe {cuisson} {taille}'
            if not PlatMenu.objects.filter(nom__iexact=nom).exists():
                try:
                    plat = Plat.objects.get(nom__iexact=nom)
                    cuisine_plat_id = plat.id
                except Plat.DoesNotExist:
                    cuisine_plat_id = None
                PlatMenu.objects.create(
                    nom=nom,
                    categorie_id=CAT_POISSONS,
                    prix=prix,
                    temps_preparation=TEMPS_PREP,
                    disponible=True,
                    cuisine_plat_id=cuisine_plat_id,
                )


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0021_add_platmenu_sol_stpierre'),
        ('cuisine', '0012_add_carpe_menus_fix_stpierre_petit'),
    ]

    operations = [
        migrations.RunPython(add_carpe_fix_stpierre, migrations.RunPython.noop),
    ]
