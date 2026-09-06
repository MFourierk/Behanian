"""
Audit et correction des tickets à paiement mixte (espèces + mobile) dont
montant_especes est à 0 alors que le contenu du ticket mentionne une part
espèces explicite.

Usage :
  python manage.py audit_tickets_mixtes          # rapport seul
  python manage.py audit_tickets_mixtes --fix    # rapport + correction auto
  python manage.py audit_tickets_mixtes --ticket TC-000385  # un seul ticket
"""
import re
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db.models import Q

from facturation.models import Ticket

MOBILE_MODES = ('wave', 'orange_money', 'mtn_money', 'moov_money', 'mobile_money', 'mobile')

# Patterns cherchés dans Ticket.contenu pour retrouver la part espèces
_PATTERNS = [
    # bar/cave :  "Especes : 10 000 F"  ou  "Especes : 10000 F"
    re.compile(r'[Ee]spece[s]?\s*:\s*([\d\s,]+)\s*F', re.IGNORECASE),
    # restaurant/piscine/espaces : '<span class="item-name">Part esp...  10 000 F'
    re.compile(r'Part\s+esp[èe]ces?</span>[^<]*<span[^>]*>([\d\s,]+)\s*F', re.IGNORECASE),
    # hôtel : "Part espèces : 10 000"
    re.compile(r'Part\s+esp[èe]ces?\s*[:\-]?\s*([\d\s,]+)\s*F', re.IGNORECASE),
]


def _extraire_especes_contenu(contenu: str):
    """Retourne le montant espèces trouvé dans le contenu du ticket, ou None."""
    for pat in _PATTERNS:
        m = pat.search(contenu)
        if m:
            raw = m.group(1).replace('\xa0', '').replace(' ', '').replace(',', '')
            try:
                return Decimal(raw)
            except InvalidOperation:
                continue
    return None


class Command(BaseCommand):
    help = 'Audit des tickets mixtes (montant_especes potentiellement manquant)'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Corriger automatiquement les anomalies détectées')
        parser.add_argument('--ticket', type=str, help='Auditer un ticket précis par numéro')

    def handle(self, *args, **options):
        fix = options['fix']
        only_num = options.get('ticket')

        qs = Ticket.objects.filter(mode_paiement__in=MOBILE_MODES, montant_especes=0)
        if only_num:
            qs = Ticket.objects.filter(numero=only_num)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n=== Audit tickets mixtes — {qs.count()} ticket(s) analysé(s) ===\n'
        ))

        anomalies = []
        for t in qs.order_by('date_creation'):
            if not t.contenu:
                continue
            montant_extrait = _extraire_especes_contenu(t.contenu)
            if montant_extrait and montant_extrait > 0:
                anomalies.append((t, montant_extrait))

        if not anomalies:
            self.stdout.write(self.style.SUCCESS('✓ Aucune anomalie détectée.'))
            return

        self.stdout.write(self.style.WARNING(f'{len(anomalies)} anomalie(s) détectée(s) :\n'))
        self.stdout.write(
            f"{'TICKET':<15} {'MODE':<15} {'TOTAL':>10} {'ESP(DB)':>10} "
            f"{'ESP(CONTENU)':>12} {'MOBILE CORRECT':>14} {'MODULE'}"
        )
        self.stdout.write('-' * 90)

        corriges = 0
        for t, esp in anomalies:
            mobile_correct = t.montant_total - esp
            flag = '← À CORRIGER' if t.montant_especes == 0 else ''
            self.stdout.write(
                f"{t.numero:<15} {t.mode_paiement:<15} {float(t.montant_total):>10.0f} "
                f"{float(t.montant_especes):>10.0f} {float(esp):>12.0f} "
                f"{float(mobile_correct):>14.0f} {t.module}  {flag}"
            )

            if fix:
                t.montant_especes = esp
                t.save(update_fields=['montant_especes'])
                corriges += 1

        self.stdout.write('')
        if fix:
            self.stdout.write(self.style.SUCCESS(f'✓ {corriges} ticket(s) corrigé(s).'))
        else:
            self.stdout.write(self.style.WARNING(
                'Relancez avec --fix pour appliquer les corrections.'
            ))

        # Résumé de l'impact sur les stats
        self.stdout.write('\n--- Impact sur les encaissements ---')
        total_esp_manquant = sum(float(esp) for _, esp in anomalies)
        total_mobile_excedent = sum(
            float(t.montant_total) for t, _ in anomalies
        ) - total_esp_manquant
        self.stdout.write(f'  Espèces sous-comptées : {total_esp_manquant:,.0f} F')
        self.stdout.write(f'  Mobile surestimé      : {total_esp_manquant:,.0f} F')
