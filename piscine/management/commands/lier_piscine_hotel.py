from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Lie les acces piscine des residents a leurs reservations hotel'

    def handle(self, *args, **options):
        cursor = connection.cursor()

        # Verifier et ajouter colonnes manquantes
        cursor.execute('PRAGMA table_info(piscine_accespiscine)')
        cols = [r[1] for r in cursor.fetchall()]

        if 'reservation_hotel_id' not in cols:
            cursor.execute('ALTER TABLE piscine_accespiscine ADD COLUMN reservation_hotel_id INTEGER REFERENCES hotel_reservation(id) ON DELETE SET NULL')
            self.stdout.write(self.style.SUCCESS('Colonne reservation_hotel_id ajoutee'))

        # Recuperer tous les acces heberges sans lien hotel (SQL direct)
        cursor.execute("""
            SELECT pa.id, pa.nom_client
            FROM piscine_accespiscine pa
            WHERE pa.type_client = 'heberge'
            AND (pa.reservation_hotel_id IS NULL OR pa.reservation_hotel_id = '')
        """)
        acces_list = cursor.fetchall()
        self.stdout.write(f'Acces heberges sans lien: {len(acces_list)}')

        for acces_id, nom_client in acces_list:
            nom = nom_client.lower().strip()

            # Chercher la reservation par nom du client
            cursor.execute("""
                SELECT r.id, r.chambre_id, ch.numero
                FROM hotel_reservation r
                JOIN hotel_client c ON r.client_id = c.id
                JOIN hotel_chambre ch ON r.chambre_id = ch.id
                WHERE r.statut IN ('en_cours', 'terminee')
                AND LOWER(TRIM(c.nom || ' ' || c.prenom)) = ?
                   OR LOWER(TRIM(c.prenom || ' ' || c.nom)) = ?
                LIMIT 1
            """, [nom, nom])
            match = cursor.fetchone()

            if not match:
                # Essai avec juste le nom de famille
                parts = nom.split()
                if parts:
                    cursor.execute("""
                        SELECT r.id, r.chambre_id, ch.numero
                        FROM hotel_reservation r
                        JOIN hotel_client c ON r.client_id = c.id
                        JOIN hotel_chambre ch ON r.chambre_id = ch.id
                        WHERE r.statut IN ('en_cours', 'terminee')
                        AND LOWER(c.nom) LIKE ?
                        LIMIT 1
                    """, [f'%{parts[-1]}%'])
                    match = cursor.fetchone()

            if not match:
                self.stdout.write(f'  Pas de reservation pour: {nom_client}')
                continue

            res_id, chambre_id, chambre_num = match

            # Lier l'acces a la reservation
            cursor.execute(
                'UPDATE piscine_accespiscine SET reservation_hotel_id = ? WHERE id = ?',
                [res_id, acces_id]
            )
            self.stdout.write(self.style.SUCCESS(f'  Lie: {nom_client} -> Ch.{chambre_num}'))

            # Recuperer les consommations piscine de cet acces
            cursor.execute("""
                SELECT produit, quantite, prix_unitaire
                FROM piscine_consommationpiscine
                WHERE acces_id = ?
            """, [acces_id])
            consos = cursor.fetchall()

            for produit, quantite, prix_unitaire in consos:
                # Verifier si deja presente dans hotel
                cursor.execute("""
                    SELECT id FROM hotel_consommation
                    WHERE reservation_id = ? AND nom LIKE ? AND type_service = 'piscine'
                """, [res_id, f'%{produit}%'])
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO hotel_consommation
                        (reservation_id, type_service, nom, quantite, prix_unitaire, date_ajout)
                        VALUES (?, 'piscine', ?, ?, ?, datetime('now'))
                    """, [res_id, f'[Piscine] {produit}', quantite, prix_unitaire])
                    self.stdout.write(f'    + {produit} x{quantite} -> Ch.{chambre_num}')

        connection.commit()
        self.stdout.write(self.style.SUCCESS('Termine'))
