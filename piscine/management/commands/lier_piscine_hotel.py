from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Lie les acces piscine des residents a leurs reservations hotel'

    def handle(self, *args, **options):
        # Verifier colonnes disponibles
        cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(piscine_accespiscine)')
        cols = [r[1] for r in cursor.fetchall()]
        self.stdout.write(f'Colonnes: {cols}')

        if 'reservation_hotel_id' not in cols:
            # Ajouter la colonne manuellement
            self.stdout.write('Ajout colonne reservation_hotel_id...')
            cursor.execute('ALTER TABLE piscine_accespiscine ADD COLUMN reservation_hotel_id INTEGER REFERENCES hotel_reservation(id) ON DELETE SET NULL')
            connection.commit()
            self.stdout.write(self.style.SUCCESS('Colonne ajoutee'))

        if 'nb_adultes' not in cols:
            cursor.execute('ALTER TABLE piscine_accespiscine ADD COLUMN nb_adultes INTEGER NOT NULL DEFAULT 1')
            cursor.execute('ALTER TABLE piscine_accespiscine ADD COLUMN nb_enfants INTEGER NOT NULL DEFAULT 0')
            connection.commit()
            self.stdout.write(self.style.SUCCESS('Colonnes nb_adultes/nb_enfants ajoutees'))

        from piscine.models import AccesPiscine, ConsommationPiscine
        from hotel.models import Reservation, Consommation as HotelConso

        acces_heberges = AccesPiscine.objects.filter(type_client='heberge', reservation_hotel__isnull=True)
        self.stdout.write(f'Acces heberges sans lien: {acces_heberges.count()}')

        for acces in acces_heberges:
            nom = acces.nom_client.lower().strip()
            match = None
            for r in Reservation.objects.filter(statut__in=['en_cours', 'terminee']).select_related('client', 'chambre'):
                if r.client.nom_complet.lower().strip() == nom:
                    match = r
                    break

            if not match:
                self.stdout.write(f'  Pas de reservation pour: {acces.nom_client}')
                continue

            acces.reservation_hotel = match
            acces.save()
            self.stdout.write(self.style.SUCCESS(f'  Lie: {acces.nom_client} -> Ch.{match.chambre.numero}'))

            for c in acces.consommations.all():
                exists = HotelConso.objects.filter(
                    reservation=match,
                    nom__contains=c.produit,
                    type_service='piscine'
                ).exists()
                if not exists:
                    HotelConso.objects.create(
                        reservation=match,
                        type_service='piscine',
                        nom=f'[Piscine] {c.produit}',
                        quantite=c.quantite,
                        prix_unitaire=c.prix_unitaire,
                    )
                    self.stdout.write(f'    + {c.produit} x{c.quantite} -> Ch.{match.chambre.numero}')

        self.stdout.write(self.style.SUCCESS('Termine'))
