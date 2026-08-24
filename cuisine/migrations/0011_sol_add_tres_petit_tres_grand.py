from django.db import migrations


def add_sol_extremes(apps, schema_editor):
    Plat = apps.get_model('cuisine', 'Plat')
    FicheTechnique = apps.get_model('cuisine', 'FicheTechnique')
    LigneFicheTechnique = apps.get_model('cuisine', 'LigneFicheTechnique')
    CategoriePlat = apps.get_model('cuisine', 'CategoriePlat')
    Ingredient = apps.get_model('cuisine', 'Ingredient')

    cat_poissons = CategoriePlat.objects.filter(nom__icontains='Poisson').first()
    ing_sol = Ingredient.objects.get(id=37)

    nouvelles = [
        # (nom, ref_ft, ref_plat, prix)
        ('Sol Braisé Très Petit', 'FT-SOL-BR-XS',  'PLT-SOL-BR-XS',  7000),
        ('Sol Braisé Très Grand', 'FT-SOL-BR-XL',  'PLT-SOL-BR-XL', 15000),
        ('Sol Sauté Très Petit',  'FT-SOL-ST-XS',  'PLT-SOL-ST-XS',  7000),
        ('Sol Sauté Très Grand',  'FT-SOL-ST-XL',  'PLT-SOL-ST-XL', 15000),
        ('Sol Frit Très Petit',   'FT-SOL-FR-XS',  'PLT-SOL-FR-XS',  7000),
        ('Sol Frit Très Grand',   'FT-SOL-FR-XL',  'PLT-SOL-FR-XL', 15000),
    ]

    for nom, ref_ft, ref_plat, prix in nouvelles:
        if not Plat.objects.filter(nom__iexact=nom).exists():
            ft, _ = FicheTechnique.objects.get_or_create(
                reference=ref_ft,
                defaults=dict(nom=nom, categorie=cat_poissons, nb_portions=1),
            )
            if not ft.lignes.filter(ingredient=ing_sol).exists():
                LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_sol, quantite=1)
            Plat.objects.create(
                nom=nom, reference=ref_plat, categorie=cat_poissons,
                prix_vente=prix, statut='disponible', fiche_technique=ft,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0010_fix_sol_stpierre_menus'),
    ]

    operations = [
        migrations.RunPython(add_sol_extremes, migrations.RunPython.noop),
    ]
