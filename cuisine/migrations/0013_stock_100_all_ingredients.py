from django.db import migrations


def set_stock_100(apps, schema_editor):
    Ingredient = apps.get_model('cuisine', 'Ingredient')
    updated = Ingredient.objects.all().update(quantite_stock=100)
    print(f'  {updated} ingrédients mis à 100')


def reverse_stock(apps, schema_editor):
    pass  # irréversible — inventaire réel à faire après


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0012_add_carpe_menus_fix_stpierre_petit'),
    ]

    operations = [
        migrations.RunPython(set_stock_100, reverse_stock),
    ]
