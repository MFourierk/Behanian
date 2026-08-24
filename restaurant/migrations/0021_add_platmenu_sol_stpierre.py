from django.db import migrations


# Catégorie "Poissons & Fruits de mer" id=10 dans restaurant.CategorieMenu
CAT_POISSONS = 10
TEMPS_PREP = 15


def add_platmenus(apps, schema_editor):
    PlatMenu = apps.get_model('restaurant', 'PlatMenu')

    # ----------------------------------------------------------------
    # 1. Mettre à jour les prix des PlatMenu Sol existants
    #    (Petit : 7000→9000, Grand : 15000→12000)
    # ----------------------------------------------------------------
    PlatMenu.objects.filter(nom__iexact='Sol Braisé Petit').update(prix=9000)
    PlatMenu.objects.filter(nom__iexact='Sol Sauté Petit').update(prix=9000)
    PlatMenu.objects.filter(nom__iexact='Sol Frit Petit').update(prix=9000)
    PlatMenu.objects.filter(nom__iexact='Sol Braisé Grand').update(prix=12000)
    PlatMenu.objects.filter(nom__iexact='Sol Sauté Grand').update(prix=12000)
    PlatMenu.objects.filter(nom__iexact='Sol Frit Grand').update(prix=12000)

    # ----------------------------------------------------------------
    # 2. Renommer St Pierre Grand→Très Grand dans PlatMenu
    # ----------------------------------------------------------------
    for cuisson in ['Braisé', 'Soupe', 'Sauté', 'Frit']:
        old = f'St Pierre {cuisson} Grand'
        new = f'St Pierre {cuisson} Très Grand'
        PlatMenu.objects.filter(nom__iexact=old, prix=17000).update(nom=new)

    # ----------------------------------------------------------------
    # 3. Créer les nouveaux PlatMenu Sol (Très Petit, Moyen, Très Grand)
    #    cuisine_plat_id = id du cuisine.Plat correspondant
    # ----------------------------------------------------------------
    sol_new = [
        # (nom, prix, cuisine_plat_id)
        ('Sol Braisé Très Petit',  7000,  157),
        ('Sol Braisé Moyen',      10000,  146),
        ('Sol Braisé Très Grand', 15000,  158),
        ('Sol Sauté Très Petit',   7000,  159),
        ('Sol Sauté Moyen',       10000,  147),
        ('Sol Sauté Très Grand',  15000,  160),
        ('Sol Frit Très Petit',    7000,  161),
        ('Sol Frit Moyen',        10000,  148),
        ('Sol Frit Très Grand',   15000,  162),
    ]
    for nom, prix, plat_id in sol_new:
        if not PlatMenu.objects.filter(nom__iexact=nom).exists():
            PlatMenu.objects.create(
                nom=nom,
                categorie_id=CAT_POISSONS,
                prix=prix,
                temps_preparation=TEMPS_PREP,
                disponible=True,
                cuisine_plat_id=plat_id,
            )

    # ----------------------------------------------------------------
    # 4. Créer les nouveaux PlatMenu St Pierre (Moyen, Grand)
    # ----------------------------------------------------------------
    stp_new = [
        ('St Pierre Braisé Moyen',  12000, 149),
        ('St Pierre Braisé Grand',  15000, 150),
        ('St Pierre Soupe Moyen',   12000, 151),
        ('St Pierre Soupe Grand',   15000, 152),
        ('St Pierre Sauté Moyen',   12000, 153),
        ('St Pierre Sauté Grand',   15000, 154),
        ('St Pierre Frit Moyen',    12000, 155),
        ('St Pierre Frit Grand',    15000, 156),
    ]
    for nom, prix, plat_id in stp_new:
        if not PlatMenu.objects.filter(nom__iexact=nom).exists():
            PlatMenu.objects.create(
                nom=nom,
                categorie_id=CAT_POISSONS,
                prix=prix,
                temps_preparation=TEMPS_PREP,
                disponible=True,
                cuisine_plat_id=plat_id,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0020_categoriemenu_parent'),
    ]

    operations = [
        migrations.RunPython(add_platmenus, migrations.RunPython.noop),
    ]
