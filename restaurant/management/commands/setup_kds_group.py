from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crée le groupe Django 'KDS' pour les serveurs et cuisiniers."

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='KDS')
        if created:
            self.stdout.write(self.style.SUCCESS("Groupe 'KDS' créé avec succès."))
        else:
            self.stdout.write("Groupe 'KDS' existe déjà — aucune modification.")
        self.stdout.write(
            "Ajoutez les serveurs/serveuses et cuisinier(e)s à ce groupe via l'admin Django "
            "ou le module Paramètres → Utilisateurs."
        )
