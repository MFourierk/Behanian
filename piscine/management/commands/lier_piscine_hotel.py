from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Lie les acces piscine des residents a leurs reservations hotel'

    def handle(self, *args, **options):
        cursor = connection.cursor()

        # Ajouter colonne si manquante
        cursor.execute('PRAGMA table_info(piscine_accespiscine)')
        cols = [r[1] for r in cursor.fetchall()]
        if 'reservation_hotel_id' not in cols:
            cursor.execute('ALTER TABLE piscine_accespiscine ADD COLUMN reservation_hotel_id INTEGER REFERENCES hotel_reservation(id) ON DELETE SET NULL')
            self.stdout.write(self.style.SUCCESS('Colonne reservation_hotel_id ajoutee'))

        # Acces heberges sans lien
        cursor.execute("SELECT id, nom_client FROM piscine_accespiscine WHERE type_client='heberge' AND reservation_hotel_id IS NULL")
        acces_list = cursor.fetchall()
        self.stdout.write(f'Acces heberges sans lien: {len(acces_list)}')

        for acces_id, nom_client in acces_list:
            nom_lower = nom_client.lower().strip()

            # Charger tous les clients et comparer en Python
            cursor.execute('SELECT id, nom, prenom FROM hotel_client')
            all_clients = cursor.fetchall()

            client_id = None
            for cid, cnom, cprenom in all_clients:
                full1 = (str(cnom) + ' ' + str(cprenom)).lower().strip()
                full2 = (str(cprenom) + ' ' + str(cnom)).lower().strip()
                if nom_lower == full1 or nom_lower == full2 or nom_lower in full1 or nom_lower in full2:
                    client_id = cid
                    break

            if not client_id:
                self.stdout.write(f'  Pas de client trouve pour: {nom_client}')
                continue

            # Chercher la reservation (utiliser %s)
            cursor.execute(
                'SELECT r.id, ch.numero FROM hotel_reservation r JOIN hotel_chambre ch ON r.chambre_id=ch.id WHERE r.client_id=%s AND (r.statut=%s OR r.statut=%s) ORDER BY r.date_arrivee DESC LIMIT 1',
                [client_id, 'en_cours', 'terminee']
            )
            res = cursor.fetchone()
            if not res:
                self.stdout.write(f'  Pas de reservation pour: {nom_client}')
                continue

            res_id, chambre_num = res
            cursor.execute('UPDATE piscine_accespiscine SET reservation_hotel_id=%s WHERE id=%s', [res_id, acces_id])
            self.stdout.write(self.style.SUCCESS(f'  Lie: {nom_client} -> Ch.{chambre_num}'))

            # Ajouter consommations dans hotel
            cursor.execute('SELECT produit, quantite, prix_unitaire FROM piscine_consommationpiscine WHERE acces_id=%s', [acces_id])
            for produit, quantite, prix in cursor.fetchall():
                cursor.execute(
                    "SELECT id FROM hotel_consommation WHERE reservation_id=%s AND nom LIKE %s AND type_service='piscine'",
                    [res_id, '%' + produit + '%']
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO hotel_consommation (reservation_id, type_service, nom, quantite, prix_unitaire, date_ajout) VALUES (%s, 'piscine', %s, %s, %s, datetime('now'))",
                        [res_id, '[Piscine] ' + produit, quantite, prix]
                    )
                    self.stdout.write(f'    + {produit} x{quantite} -> Ch.{chambre_num}')

        connection.commit()
        self.stdout.write(self.style.SUCCESS('Termine'))
