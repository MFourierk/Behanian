from django.db import migrations


def add_carpe_fix_stpierre(apps, schema_editor):
    Plat = apps.get_model('cuisine', 'Plat')
    FicheTechnique = apps.get_model('cuisine', 'FicheTechnique')
    LigneFicheTechnique = apps.get_model('cuisine', 'LigneFicheTechnique')
    CategoriePlat = apps.get_model('cuisine', 'CategoriePlat')
    Ingredient = apps.get_model('cuisine', 'Ingredient')

    cat_poissons = CategoriePlat.objects.get(id=10)
    ing_carpe = Ingredient.objects.get(id=12)

    # ----------------------------------------------------------------
    # Carpe — créer Petit (10 000), Moyen (12 000), Grand (15 000)
    # Cuissons : Braisée, Frit, Sautée, Soupe
    # ----------------------------------------------------------------
    carpe_data = []
    for cuisson, code in [('Braisée', 'BR'), ('Frit', 'FR'), ('Sautée', 'ST'), ('Soupe', 'SP')]:
        carpe_data += [
            (f'Carpe {cuisson} Petit',  f'FT-CARPE-{code}-PETIT',  f'PLT-CARPE-{code}-PETIT',  10000),
            (f'Carpe {cuisson} Moyen',  f'FT-CARPE-{code}-MOYEN',  f'PLT-CARPE-{code}-MOYEN',  12000),
            (f'Carpe {cuisson} Grand',  f'FT-CARPE-{code}-GRAND',  f'PLT-CARPE-{code}-GRAND',  15000),
        ]

    for nom, ref_ft, ref_plat, prix in carpe_data:
        if not Plat.objects.filter(nom__iexact=nom).exists():
            ft, _ = FicheTechnique.objects.get_or_create(
                reference=ref_ft,
                defaults=dict(nom=nom, categorie=cat_poissons, nb_portions=1),
            )
            if not ft.lignes.filter(ingredient=ing_carpe).exists():
                LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_carpe, quantite=1)
            Plat.objects.create(
                nom=nom, reference=ref_plat, categorie=cat_poissons,
                prix_vente=prix, statut='disponible', fiche_technique=ft,
            )

    # ----------------------------------------------------------------
    # St Pierre Petit — 9 000 → 10 000
    # ----------------------------------------------------------------
    for cuisson in ['Braisé', 'Soupe', 'Sauté', 'Frit']:
        Plat.objects.filter(nom__iexact=f'St Pierre {cuisson} Petit', prix_vente=9000).update(prix_vente=10000)


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0011_sol_add_tres_petit_tres_grand'),
    ]

    operations = [
        migrations.RunPython(add_carpe_fix_stpierre, migrations.RunPython.noop),
    ]
