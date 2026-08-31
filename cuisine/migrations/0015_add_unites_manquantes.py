from django.db import migrations


UNITES = [
    # (nom, abreviation, type_unite)
    ('Boule',   'boul',  'piece'),
    ('Sachet',  'sach',  'piece'),
    ('Boîte',   'bte',   'piece'),
    ('Brique',  'briq',  'piece'),
]


def ajouter_unites(apps, schema_editor):
    UniteIngredient = apps.get_model('cuisine', 'UniteIngredient')
    for nom, abr, type_u in UNITES:
        if not UniteIngredient.objects.filter(abreviation=abr).exists():
            UniteIngredient.objects.create(nom=nom, abreviation=abr, type_unite=type_u)


class Migration(migrations.Migration):

    dependencies = [
        ('cuisine', '0014_add_unite_piece_fix_kg_doublon'),
    ]

    operations = [
        migrations.RunPython(ajouter_unites, migrations.RunPython.noop),
    ]
