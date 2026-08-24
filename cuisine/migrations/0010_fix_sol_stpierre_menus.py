from django.db import migrations


def fix_sol_stpierre(apps, schema_editor):
    Plat = apps.get_model('cuisine', 'Plat')
    FicheTechnique = apps.get_model('cuisine', 'FicheTechnique')
    LigneFicheTechnique = apps.get_model('cuisine', 'LigneFicheTechnique')
    CategoriePlat = apps.get_model('cuisine', 'CategoriePlat')
    Ingredient = apps.get_model('cuisine', 'Ingredient')

    cat_poissons = CategoriePlat.objects.filter(nom__icontains='Poisson').first()
    ing_sol = Ingredient.objects.get(id=37)
    ing_stpierre = Ingredient.objects.get(id=39)

    # ----------------------------------------------------------------
    # SOL — corriger les prix des Petit et Grand existants
    # ----------------------------------------------------------------
    for cuisine in ['Braisé', 'Sauté', 'Frit']:
        Plat.objects.filter(
            nom__iexact=f'Sol {cuisine} Petit'
        ).update(prix_vente=9000)
        Plat.objects.filter(
            nom__iexact=f'Sol {cuisine} Grand'
        ).exclude(prix_vente=12000).update(prix_vente=12000)

    # ----------------------------------------------------------------
    # SOL — créer Moyen (10 000 F) si absent
    # ----------------------------------------------------------------
    for cuisine, ref_ft, ref_plat in [
        ('Braisé', 'FT-SOL-BR-MOYEN',  'PLT-SOL-BR-MOYEN'),
        ('Sauté',  'FT-SOL-ST-MOYEN',  'PLT-SOL-ST-MOYEN'),
        ('Frit',   'FT-SOL-FR-MOYEN',  'PLT-SOL-FR-MOYEN'),
    ]:
        nom = f'Sol {cuisine} Moyen'
        if not Plat.objects.filter(nom__iexact=nom).exists():
            ft, _ = FicheTechnique.objects.get_or_create(
                reference=ref_ft,
                defaults=dict(nom=nom, categorie=cat_poissons, nb_portions=1),
            )
            if not ft.lignes.filter(ingredient=ing_sol).exists():
                LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_sol, quantite=1)
            Plat.objects.create(
                nom=nom, reference=ref_plat, categorie=cat_poissons,
                prix_vente=10000, statut='disponible', fiche_technique=ft,
            )

    # ----------------------------------------------------------------
    # ST PIERRE — renommer Grand → Très Grand (si pas encore fait)
    # ----------------------------------------------------------------
    for cuisine in ['Braisé', 'Soupe', 'Sauté', 'Frit']:
        old = f'St Pierre {cuisine} Grand'
        new = f'St Pierre {cuisine} Très Grand'
        if Plat.objects.filter(nom__iexact=old, prix_vente=17000).exists():
            Plat.objects.filter(nom__iexact=old, prix_vente=17000).update(nom=new)
            FicheTechnique.objects.filter(nom__iexact=old).update(nom=new)

    # ----------------------------------------------------------------
    # ST PIERRE — créer Moyen (12 000 F) et Grand (15 000 F) si absents
    # ----------------------------------------------------------------
    stpierre_data = []
    for cuisine in ['Braisé', 'Soupe', 'Sauté', 'Frit']:
        code = cuisine[:2].upper()
        stpierre_data += [
            (f'St Pierre {cuisine} Moyen', f'FT-STP-{code}-MOYEN', f'PLT-STP-{code}-MOYEN', 12000),
            (f'St Pierre {cuisine} Grand', f'FT-STP-{code}-GRAND', f'PLT-STP-{code}-GRAND', 15000),
        ]

    for nom, ref_ft, ref_plat, prix in stpierre_data:
        if not Plat.objects.filter(nom__iexact=nom).exists():
            ft, _ = FicheTechnique.objects.get_or_create(
                reference=ref_ft,
                defaults=dict(nom=nom, categorie=cat_poissons, nb_portions=1),
            )
            if not ft.lignes.filter(ingredient=ing_stpierre).exists():
                LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_stpierre, quantite=1)
            Plat.objects.create(
                nom=nom, reference=ref_plat, categorie=cat_poissons,
                prix_vente=prix, statut='disponible', fiche_technique=ft,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0009_add_sol_stpierre_menus'),
    ]

    operations = [
        migrations.RunPython(fix_sol_stpierre, migrations.RunPython.noop),
    ]
