from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from .models import Table, Reservation, Commande
from django.utils.dateparse import parse_datetime

@login_required
@require_POST
def create_reservation(request):
    """Crée une nouvelle réservation"""
    try:
        data = json.loads(request.body)
        table_id = data.get('table_id')
        client_nom = data.get('client_nom')
        date_str = data.get('date_reservation')
        nb_personnes = int(data.get('nombre_personnes', 1))
        telephone = data.get('telephone', '')
        note = data.get('note', '')

        if not all([table_id, client_nom, date_str]):
             return JsonResponse({'success': False, 'message': 'Données manquantes'})

        table = get_object_or_404(Table, id=table_id)
        
        date_res = parse_datetime(date_str)
        if not date_res:
             return JsonResponse({'success': False, 'message': 'Date invalide'})
             
        # Création réservation
        Reservation.objects.create(
            table=table,
            client_nom=client_nom,
            client_telephone=telephone,
            date_reservation=date_res,
            nombre_personnes=nb_personnes,
            note=note,
            statut='confirmee'
        )
        
        # On met la table en statut réservée
        table.statut = 'reservee'
        table.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def update_reservation_status(request):
    """Met à jour le statut d'une réservation"""
    try:
        data = json.loads(request.body)
        reservation_id = data.get('reservation_id')
        new_status = data.get('status') # 'terminee', 'annulee', 'confirmee'
        
        if not reservation_id or not new_status:
            return JsonResponse({'success': False, 'message': 'Données manquantes'})

        res = get_object_or_404(Reservation, id=reservation_id)
        res.statut = new_status
        res.save()
        
        if new_status == 'terminee':
            # Create a new active order for this table
            commande, created = Commande.objects.get_or_create(
                table=res.table,
                statut='en_preparation',
                defaults={
                    'serveur': request.user,
                    'nom_client': res.client_nom,
                    'total': 0
                }
            )
            # Mark table as occupied
            res.table.statut = 'occupee'
            res.table.save()
            return JsonResponse({'success': True, 'commande_id': commande.id})
            
        elif new_status == 'annulee':
            # If cancelled, free the table if it was reserved
            if res.table.statut == 'reservee':
                res.table.statut = 'disponible'
                res.table.save()
                
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
