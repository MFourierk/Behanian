from django.db import migrations


def ajouter_piece_et_corriger_kg(apps, schema_editor):
    UniteIngredient = apps.get_model('cuisine', 'UniteIngredient')

    # Créer "Pièce" si absent
    if not UniteIngredient.objects.filter(abreviation='pce').exists():
        UniteIngredient.objects.create(
            nom='Pièce',
            abreviation='pce',
            type_unite='piece',
        )

    # Corriger le doublon Kilogramme : garder le premier, supprimer l'autre
    kgs = UniteIngredient.objects.filter(nom__iexact='kilogramme').order_by('id')
    if kgs.count() > 1:
        Ingredient = apps.get_model('cuisine', 'Ingredient')
        kg_a_garder = kgs.first()
        for kg_doublon in kgs[1:]:
            # Réassigner les ingrédients pointant sur le doublon
            Ingredient.objects.filter(unite_stock=kg_doublon).update(unite_stock=kg_a_garder)
            Ingredient.objects.filter(unite_recette=kg_doublon).update(unite_recette=kg_a_garder)
            kg_doublon.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0013_stock_100_all_ingredients'),
    ]

    operations = [
        migrations.RunPython(
            ajouter_piece_et_corriger_kg,
            migrations.RunPython.noop,
        ),
    ]
