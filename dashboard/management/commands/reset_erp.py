"""
python manage.py reset_erp [--type partiel|complet] [--yes]

Commande de remise à zéro utilisable depuis le terminal du serveur.
Pratique pour les scripts de déploiement et la maintenance en production.

Exemples :
  python manage.py reset_erp --type partiel --yes
  python manage.py reset_erp --type complet --yes
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Remise à zéro du système ERP Behanian (partielle ou totale)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['partiel', 'complet'],
            default='partiel',
            help="Type de remise : partiel (transactions seulement) ou complet (tout sauf structure)."
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help="Confirmer sans prompt interactif (pour les scripts automatisés)."
        )

    def handle(self, *args, **options):
        type_reset = options['type']
        auto_yes   = options['yes']

        self.stdout.write(self.style.WARNING(
            f"\n{'='*60}\n"
            f"  BEHANIAN ERP — Remise à Zéro {type_reset.upper()}\n"
            f"{'='*60}"
        ))

        if type_reset == 'complet':
            self.stdout.write(self.style.ERROR(
                "\n⚠️  ATTENTION : La remise TOTALE va supprimer :\n"
                "   • Toutes les transactions\n"
                "   • Tous les stocks\n"
                "   • Tout le référentiel (articles, plats, boissons, utilisateurs…)\n"
                "   Ne conserve que l'infrastructure physique et les superusers.\n"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "\n📋 La remise PARTIELLE va supprimer :\n"
                "   • Toutes les transactions (commandes, réservations, tickets…)\n"
                "   • Les mouvements de stock\n"
                "   ✅ Conserve : articles, plats, boissons, stocks, utilisateurs\n"
            ))

        if not auto_yes:
            confirm = input(
                f"\nConfirmez la remise {type_reset} ? Saisissez "
                f"{'RESET TOTAL' if type_reset == 'complet' else 'CONFIRMER'} : "
            )
            expected = 'RESET TOTAL' if type_reset == 'complet' else 'CONFIRMER'
            if confirm.strip().upper() != expected:
                raise CommandError("Confirmation incorrecte. Opération annulée.")

        # Récupérer le premier superuser pour le journal
        superuser = User.objects.filter(is_superuser=True).first()

        try:
            from dashboard.reset_actions import reset_partiel, reset_complet, get_counts, get_total

            counts = get_counts()
            self.stdout.write(f"\n📊 Transactions avant reset : {get_total(counts)}")

            self.stdout.write("\n⏳ Backup en cours…")
            if type_reset == 'partiel':
                _, backup_path = reset_partiel(user=superuser)
            else:
                _, backup_path = reset_complet(user=superuser)

            if backup_path:
                self.stdout.write(f"   ✅ Backup : {backup_path}")

            counts_apres = get_counts()
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Remise à zéro {type_reset} effectuée avec succès.\n"
                    f"   Transactions restantes : {get_total(counts_apres)}\n"
                )
            )

        except Exception as e:
            raise CommandError(f"Échec de la remise à zéro : {e}")
