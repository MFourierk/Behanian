from django.db import migrations


def ensure_services(apps, schema_editor):
    Service = apps.get_model('facturation', 'Service')
    for nom in ["Hôtel", "Restaurant", "Cave", "Bar", "Piscine", "Espaces Location"]:
        Service.objects.get_or_create(nom=nom)


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0021_avoir_updated_at_facture_updated_at_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_services, migrations.RunPython.noop),
    ]
