from django.db import migrations


def set_stock_100(apps, schema_editor):
    BoissonBar = apps.get_model('bar', 'BoissonBar')
    updated = BoissonBar.objects.all().update(quantite_stock=100)
    print(f'  {updated} boissons mises à 100')


def reverse_stock(apps, schema_editor):
    pass  # irréversible — inventaire réel à faire après


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0017_ventecave_lignevantecave'),
    ]

    operations = [
        migrations.RunPython(set_stock_100, reverse_stock),
    ]
