from utils.permissions import require_module_access
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count, F
from decimal import Decimal
import json

from .models import EspaceEvenementiel, ReservationEspace


@require_module_access('espaces')
def espaces_index(request):
    today = timezone.now().date()

    espaces = EspaceEvenementiel.objects.all()
    reservations_actives = ReservationEspace.objects.filter(
        statut__in=['confirmee', 'en_cours']
    ).select_related('espace', 'creee_par', 'reservation_hotel__client', 'reservation_hotel__chambre').order_by('-date_debut')

    # Stats — statut_reel calculé dynamiquement
    total_espaces = espaces.count()
    espaces_dispo = sum(1 for e in espaces if e.statut_reel == 'disponible')
    reservations_jour = ReservationEspace.objects.filter(date_debut__date=today).count()
    recette_mois = ReservationEspace.objects.filter(
        statut__in=['terminee', 'en_cours', 'confirmee'],
        date_debut__month=today.month, date_debut__year=today.year
    ).aggregate(s=Sum(F('prix_total') - F('remise')))['s'] or 0

    # Résidents hôtel pour lier
    from hotel.models import Reservation as HotelReservation
    residents = HotelReservation.objects.filter(statut='en_cours').select_related('client', 'chambre')

    context = {
        'espaces': espaces,
        'reservations_actives': reservations_actives,
        'total_espaces': total_espaces,
        'espaces_dispo': espaces_dispo,
        'reservations_jour': reservations_jour,
        'recette_mois': int(recette_mois),
        'residents': residents,
    }
    return render(request, 'espaces_evenementiels/index.html', context)


@require_module_access('espaces')
@require_POST
def api_reserver(request):
    """Créer une réservation d'espace."""
    try:
        data = json.loads(request.body)
        espace_id = data.get('espace_id')
        nom_client = data.get('nom_client', '').strip()
        type_client = data.get('type_client', 'particulier')
        telephone = data.get('telephone', '').strip()
        type_evenement = data.get('type_evenement', '').strip()
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        nombre_personnes = int(data.get('nombre_personnes', 1))
        remise = Decimal(str(data.get('remise', 0)))
        avance = Decimal(str(data.get('avance', 0)))
        commentaire = data.get('commentaire', '')
        reservation_hotel_id = data.get('reservation_hotel_id')

        if not all([espace_id, nom_client, date_debut, date_fin]):
            return JsonResponse({'success': False, 'error': 'Champs requis manquants'})

        espace = get_object_or_404(EspaceEvenementiel, id=espace_id)

        from django.utils.dateparse import parse_datetime
        dt_debut = parse_datetime(date_debut)
        dt_fin = parse_datetime(date_fin)
        if not dt_debut or not dt_fin or dt_fin <= dt_debut:
            return JsonResponse({'success': False, 'error': 'Dates invalides'})

        # Vérifier chevauchement avec réservations existantes
        # Un chevauchement existe si : debut_existant < dt_fin ET fin_existant > dt_debut
        chevauchements = ReservationEspace.objects.filter(
            espace_id=espace_id,
            statut__in=['confirmee', 'en_cours'],
            date_debut__lt=dt_fin,
            date_fin__gt=dt_debut,
        )
        if chevauchements.exists():
            res_conflict = chevauchements.first()
            return JsonResponse({
                'success': False,
                'error': (
                    f"Cet espace est déjà réservé du "
                    f"{res_conflict.date_debut.strftime('%d/%m/%Y')} au "
                    f"{res_conflict.date_fin.strftime('%d/%m/%Y')} "
                    f"par {res_conflict.nom_client} ({res_conflict.type_evenement})."
                )
            })

        # Calculer prix total
        duree_h = (dt_fin - dt_debut).total_seconds() / 86400
        prix_total = Decimal(str(round(duree_h, 2))) * espace.prix_jour

        reservation_hotel = None
        if type_client == 'heberge' and reservation_hotel_id:
            from hotel.models import Reservation as HotelRes
            try:
                reservation_hotel = HotelRes.objects.get(id=reservation_hotel_id, statut='en_cours')
                nom_client = reservation_hotel.client.nom_complet
            except HotelRes.DoesNotExist:
                pass

        res = ReservationEspace.objects.create(
            espace=espace,
            nom_client=nom_client,
            type_client=type_client,
            telephone=telephone,
            type_evenement=type_evenement,
            date_debut=dt_debut,
            date_fin=dt_fin,
            nombre_personnes=nombre_personnes,
            prix_total=prix_total,
            remise=remise,
            avance=avance,
            commentaire=commentaire,
            statut='confirmee',
            reservation_hotel=reservation_hotel,
            creee_par=request.user,
        )

        return JsonResponse({
            'success': True,
            'reservation_id': res.id,
            'prix_total': float(prix_total),
            'message': f'Réservation créée — {nom_client} / {espace.nom}'
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('espaces')
@require_POST
def api_encaisser(request, reservation_id):
    """Encaisser une réservation d'espace."""
    try:
        from facturation.models import Ticket, generate_ticket_numero
        from django.template.loader import render_to_string

        res = get_object_or_404(ReservationEspace, id=reservation_id)
        data = json.loads(request.body)
        mode_paiement = data.get('mode_paiement', 'especes')
        montant_recu = Decimal(str(data.get('montant_recu', 0)))
        sur_chambre = data.get('sur_chambre', False)

        montant_net = res.prix_total - res.remise
        restant = montant_net - res.avance

        # Mode CHAMBRE
        if sur_chambre and res.reservation_hotel:
            from hotel.models import Consommation as HotelConso
            HotelConso.objects.create(
                reservation=res.reservation_hotel,
                type_service='espace',
                espace=res.espace,
                nom=f'[Espace] {res.espace.nom} — {res.type_evenement}',
                quantite=1,
                prix_unitaire=restant,
            )
            res.statut = 'terminee'
            res.save()
            lignes = [
                {'nom': f'{res.espace.nom} ({res.duree_jours}h)', 'total': float(montant_net)},
            ]
            if res.avance > 0:
                lignes.append({'nom': 'Avance déjà perçue', 'total': -float(res.avance)})
            return JsonResponse({
                'success': True, 'sur_chambre': True,
                'chambre_nom': f'Ch. {res.reservation_hotel.chambre.numero} — {res.reservation_hotel.client.nom_complet}',
                'lignes': lignes, 'total': float(restant),
                'message': f'Ajouté à la chambre {res.reservation_hotel.chambre.numero}'
            })

        # Mode PAIEMENT DIRECT
        contenu = f'<div class="row"><span class="item-name">{res.espace.nom} — {res.type_evenement} ({res.duree_jours}h)</span><span class="item-price">{int(montant_net):,} F</span></div>'
        if res.avance > 0:
            contenu += f'<div class="row"><span class="item-name">Avance déjà perçue</span><span class="item-price">-{int(res.avance):,} F</span></div>'

        ticket = Ticket.objects.create(
            numero=generate_ticket_numero(), module='espace',
            montant_total=restant, montant_paye=montant_recu,
            mode_paiement=mode_paiement, cree_par=request.user,
            contenu=contenu, imprime=True,
        )
        ticket_html = render_to_string('facturation/ticket_print_thermal.html', {
            'ticket': ticket,
            'serveur': request.user.get_full_name() or request.user.username,
        })
        res.statut = 'terminee'
        res.save()
        return JsonResponse({
            'success': True, 'sur_chambre': False,
            'ticket_html': ticket_html,
            'total': float(restant),
            'rendu': float(max(Decimal('0'), montant_recu - restant)),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('espaces')
def api_espace_detail(request, espace_id):
    """Détails d'un espace pour le TPE."""
    espace = get_object_or_404(EspaceEvenementiel, id=espace_id)
    return JsonResponse({
        'id': espace.id,
        'nom': espace.nom,
        'type': espace.get_type_espace_display(),
        'capacite': espace.capacite,
        'prix_heure': float(espace.prix_jour),
        'equipements': [e for e, v in {
            'Projecteur': espace.projecteur, 'WiFi': espace.wifi,
            'Clim': espace.climatisation, 'Sono': espace.sonorisation,
            'Déco': espace.decoration, 'Éclairage': espace.eclairage,
            'Tentes': espace.tentes, 'Parking': espace.parking,
        }.items() if v],
        'description': espace.description or '',
        'image': espace.image.url if espace.image else None,
    })
