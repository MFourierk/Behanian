"""
Lier manuellement les accès piscine des résidents à leurs réservations hôtel
Lancer : Get-Content scripts\lier_piscine_hotel.py | python manage.py shell
"""
from piscine.models import AccesPiscine, ConsommationPiscine
from hotel.models import Reservation, Consommation as HotelConso
from django.db import connection

# Vérifier que les colonnes existent
cursor = connection.cursor()
cursor.execute('PRAGMA table_info(piscine_accespiscine)')
cols = [r[1] for r in cursor.fetchall()]
print('Colonnes disponibles:', cols)

if 'reservation_hotel_id' not in cols:
    print('ERREUR: migration 0004 non appliquee. Lance: python manage.py migrate piscine 0004')
else:
    # Trouver les accès hébergés sans réservation liée
    acces_heberges = AccesPiscine.objects.filter(type_client='heberge', reservation_hotel__isnull=True)
    print(f'Acces heberges sans lien hotel: {acces_heberges.count()}')

    for acces in acces_heberges:
        # Chercher la réservation correspondante par nom du client
        nom = acces.nom_client.lower().strip()
        reservations = Reservation.objects.filter(statut__in=['en_cours', 'terminee'])
        match = None
        for r in reservations:
            if r.client.nom_complet.lower().strip() == nom:
                match = r
                break
        if match:
            acces.reservation_hotel = match
            acces.save()
            print(f'  Lie: {acces.nom_client} -> Ch.{match.chambre.numero}')

            # Créer les consommations manquantes dans hotel
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
                    print(f'    + {c.produit} x{c.quantite} ajoutee a la chambre {match.chambre.numero}')
        else:
            print(f'  Aucune reservation trouvee pour: {acces.nom_client}')

    print('Termine')
