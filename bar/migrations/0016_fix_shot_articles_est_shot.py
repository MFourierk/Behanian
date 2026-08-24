from django.db import migrations


def fix_shot_articles(apps, schema_editor):
    """
    Relie les articles shot/tournée à leur parent via est_shot=True et shot_parent.
    Corrige les articles dont ces champs ont été perdus.
    """
    ParametrageShot = apps.get_model('bar', 'ParametrageShot')
    BoissonBar = apps.get_model('bar', 'BoissonBar')

    for param in ParametrageShot.objects.select_related('boisson', 'article_shot', 'article_tournee'):
        if param.article_shot:
            BoissonBar.objects.filter(pk=param.article_shot_id).update(
                est_shot=True,
                shot_parent_id=param.boisson_id,
                shot_ml=param.volume_shot_ml,
                disponible=True,
                statut='actif',
            )
        if param.article_tournee:
            BoissonBar.objects.filter(pk=param.article_tournee_id).update(
                est_shot=True,
                shot_parent_id=param.boisson_id,
                shot_ml=param.volume_shot_ml * 2,
                disponible=True,
                statut='actif',
            )


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0015_boissonbar_shot_fields_parametrage_articles'),
    ]

    operations = [
        migrations.RunPython(fix_shot_articles, migrations.RunPython.noop),
    ]
