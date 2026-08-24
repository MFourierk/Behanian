from django.db import migrations


def add_sol_stpierre_menus(apps, schema_editor):
    Plat = apps.get_model('cuisine', 'Plat')
    FicheTechnique = apps.get_model('cuisine', 'FicheTechnique')
    LigneFicheTechnique = apps.get_model('cuisine', 'LigneFicheTechnique')
    CategoriePlat = apps.get_model('cuisine', 'CategoriePlat')
    Ingredient = apps.get_model('cuisine', 'Ingredient')

    cat_poissons = CategoriePlat.objects.get(nom__icontains='Poissons')
    ing_sol = Ingredient.objects.get(id=37)      # Sol
    ing_stpierre = Ingredient.objects.get(id=39)  # St Pierre

    # ----------------------------------------------------------------
    # 1. SOL — mettre à jour Petit (7000→9000) et Grand (15000→12000)
    # ----------------------------------------------------------------
    Plat.objects.filter(nom='Sol Braisé Petit').update(prix_vente=9000)
    Plat.objects.filter(nom='Sol Sauté Petit').update(prix_vente=9000)
    Plat.objects.filter(nom='Sol Frit Petit').update(prix_vente=9000)
    Plat.objects.filter(nom='Sol Braisé Grand').update(prix_vente=12000)
    Plat.objects.filter(nom='Sol Sauté Grand').update(prix_vente=12000)
    Plat.objects.filter(nom='Sol Frit Grand').update(prix_vente=12000)

    # ----------------------------------------------------------------
    # 2. SOL — ajouter Moyen (10 000 FCFA) pour les 3 cuissons
    # ----------------------------------------------------------------
    sol_moyen = [
        ('Sol Braisé Moyen',  'FT-SOL-BR-MOYEN', 'PLT-SOL-BR-MOYEN'),
        ('Sol Sauté Moyen',   'FT-SOL-ST-MOYEN', 'PLT-SOL-ST-MOYEN'),
        ('Sol Frit Moyen',    'FT-SOL-FR-MOYEN', 'PLT-SOL-FR-MOYEN'),
    ]
    for nom, ref_ft, ref_plat in sol_moyen:
        ft = FicheTechnique.objects.create(
            nom=nom,
            reference=ref_ft,
            categorie=cat_poissons,
            nb_portions=1,
        )
        LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_sol, quantite=1)
        Plat.objects.create(
            nom=nom,
            reference=ref_plat,
            categorie=cat_poissons,
            prix_vente=10000,
            statut='disponible',
            fiche_technique=ft,
        )

    # ----------------------------------------------------------------
    # 3. ST PIERRE — renommer Grand→Très Grand pour libérer le nom
    # ----------------------------------------------------------------
    rename_map = {
        'St Pierre Braisé Grand': 'St Pierre Braisé Très Grand',
        'St Pierre Soupe Grand':  'St Pierre Soupe Très Grand',
        'St Pierre Sauté Grand':  'St Pierre Sauté Très Grand',
        'St Pierre Frit Grand':   'St Pierre Frit Très Grand',
    }
    for old_nom, new_nom in rename_map.items():
        Plat.objects.filter(nom=old_nom).update(nom=new_nom)
    # Même chose pour les FTs liées
    for old_nom, new_nom in rename_map.items():
        FicheTechnique.objects.filter(nom=old_nom).update(nom=new_nom)

    # ----------------------------------------------------------------
    # 4. ST PIERRE — ajouter Moyen (12 000) et Grand (15 000) × 4 cuissons
    # ----------------------------------------------------------------
    stpierre_new = [
        ('St Pierre Braisé Moyen',  'FT-STP-BR-MOYEN', 'PLT-STP-BR-MOYEN', 12000),
        ('St Pierre Braisé Grand',  'FT-STP-BR-GRAND', 'PLT-STP-BR-GRAND', 15000),
        ('St Pierre Soupe Moyen',   'FT-STP-SP-MOYEN', 'PLT-STP-SP-MOYEN', 12000),
        ('St Pierre Soupe Grand',   'FT-STP-SP-GRAND', 'PLT-STP-SP-GRAND', 15000),
        ('St Pierre Sauté Moyen',   'FT-STP-ST-MOYEN', 'PLT-STP-ST-MOYEN', 12000),
        ('St Pierre Sauté Grand',   'FT-STP-ST-GRAND', 'PLT-STP-ST-GRAND', 15000),
        ('St Pierre Frit Moyen',    'FT-STP-FR-MOYEN', 'PLT-STP-FR-MOYEN', 12000),
        ('St Pierre Frit Grand',    'FT-STP-FR-GRAND', 'PLT-STP-FR-GRAND', 15000),
    ]
    for nom, ref_ft, ref_plat, prix in stpierre_new:
        ft = FicheTechnique.objects.create(
            nom=nom,
            reference=ref_ft,
            categorie=cat_poissons,
            nb_portions=1,
        )
        LigneFicheTechnique.objects.create(fiche=ft, ingredient=ing_stpierre, quantite=1)
        Plat.objects.create(
            nom=nom,
            reference=ref_plat,
            categorie=cat_poissons,
            prix_vente=prix,
            statut='disponible',
            fiche_technique=ft,
        )


def reverse_menus(apps, schema_editor):
    Plat = apps.get_model('cuisine', 'Plat')
    FicheTechnique = apps.get_model('cuisine', 'FicheTechnique')

    # Supprimer les nouveaux
    for ref in [
        'PLT-SOL-BR-MOYEN', 'PLT-SOL-ST-MOYEN', 'PLT-SOL-FR-MOYEN',
        'PLT-STP-BR-MOYEN', 'PLT-STP-BR-GRAND',
        'PLT-STP-SP-MOYEN', 'PLT-STP-SP-GRAND',
        'PLT-STP-ST-MOYEN', 'PLT-STP-ST-GRAND',
        'PLT-STP-FR-MOYEN', 'PLT-STP-FR-GRAND',
    ]:
        Plat.objects.filter(reference=ref).delete()
    for ref in [
        'FT-SOL-BR-MOYEN', 'FT-SOL-ST-MOYEN', 'FT-SOL-FR-MOYEN',
        'FT-STP-BR-MOYEN', 'FT-STP-BR-GRAND',
        'FT-STP-SP-MOYEN', 'FT-STP-SP-GRAND',
        'FT-STP-ST-MOYEN', 'FT-STP-ST-GRAND',
        'FT-STP-FR-MOYEN', 'FT-STP-FR-GRAND',
    ]:
        FicheTechnique.objects.filter(reference=ref).delete()

    # Restaurer les anciens prix Sol
    Plat.objects.filter(nom='Sol Braisé Petit').update(prix_vente=7000)
    Plat.objects.filter(nom='Sol Sauté Petit').update(prix_vente=7000)
    Plat.objects.filter(nom='Sol Frit Petit').update(prix_vente=7000)
    Plat.objects.filter(nom='Sol Braisé Grand').update(prix_vente=15000)
    Plat.objects.filter(nom='Sol Sauté Grand').update(prix_vente=15000)
    Plat.objects.filter(nom='Sol Frit Grand').update(prix_vente=15000)

    # Re-renommer Très Grand → Grand
    for new_nom, old_nom in {
        'St Pierre Braisé Très Grand': 'St Pierre Braisé Grand',
        'St Pierre Soupe Très Grand':  'St Pierre Soupe Grand',
        'St Pierre Sauté Très Grand':  'St Pierre Sauté Grand',
        'St Pierre Frit Très Grand':   'St Pierre Frit Grand',
    }.items():
        Plat.objects.filter(nom=new_nom).update(nom=old_nom)
        FicheTechnique.objects.filter(nom=new_nom).update(nom=old_nom)


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0008_alter_ingredient_facteur_conversion'),
    ]

    operations = [
        migrations.RunPython(add_sol_stpierre_menus, reverse_menus),
    ]
