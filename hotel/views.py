import json
from utils.permissions import require_module_access
from .models import Chambre, Client, Reservation, Consommation
from facturation.models import Ticket, generate_ticket_numero
from decimal import Decimal
from bar.models import BoissonBar
from restaurant.models import PlatMenu
from espaces_evenementiels.models import EspaceEvenementiel
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_module_access('hotel')
def api_revenus(request):
    """API JSON — revenus chambres du jour (reservations terminées aujourd'hui)"""
    from django.utils import timezone as tz
    aujourd_hui = tz.now().date()
    # Réservations terminées aujourd'hui (check-out effectué)
    reservations_terminees = Reservation.objects.filter(
        statut='terminee',
        date_modification__date=aujourd_hui
    )
    total = sum(r.get_total_general() for r in reservations_terminees)
    return JsonResponse({
        'chambres': int(total),
        'total':    int(total),
        'count':    reservations_terminees.count(),
    })


@require_module_access('hotel')
def hotel_index(request):
    """Vue principale de gestion de l'hôtel"""
    
    # --- AUTO-CORRECTION DES STATUTS CHAMBRES ---
    # 1. Reset 'reservation'/'disponible' -> 'disponible' (si pas maintenance)
    # Cela permet de nettoyer les vieux statuts
    Chambre.objects.exclude(statut__in=['maintenance', 'occupee']).update(statut='disponible')
    
    # 2. Appliquer 'occupee' pour les séjours en cours
    active_reservations = Reservation.objects.filter(statut='en_cours')
    for res in active_reservations:
        if res.chambre.statut != 'occupee':
            res.chambre.statut = 'occupee'
            res.chambre.save()
            
    # 3. Appliquer 'reservation' pour les arrivées AUJOURD'HUI (qui ne sont pas encore checked-in)
    today = timezone.now().date()
    arrivals_today = Reservation.objects.filter(
        statut='confirmee', 
        date_arrivee=today
    )
    for res in arrivals_today:
        if res.chambre.statut == 'disponible': # Ne pas écraser maintenance ou occupée
            res.chambre.statut = 'reservation'
            res.chambre.save()
    # ---------------------------------------------

    # Statistiques
    total_chambres = Chambre.objects.count()
    chambres_disponibles = Chambre.objects.filter(statut='disponible').count()
    chambres_occupees = Chambre.objects.filter(statut='occupee').count()
    chambres_maintenance = Chambre.objects.filter(statut='maintenance').count()
    chambres_reservees = Chambre.objects.filter(statut='reservation').count()
    
    # Liste des chambres (Read Only for Hotel Module)
    chambres = Chambre.objects.all().order_by('numero')
    
    # Onglet Réservations (En attente et Confirmées)
    reservations_attente = Reservation.objects.filter(statut='en_attente').order_by('date_arrivee')
    reservations_confirmees = Reservation.objects.filter(statut='confirmee').order_by('date_arrivee')
    
    # Liste des arrivées du jour (pour Check-in)
    # On considère les réservations confirmées ET en attente qui arrivent aujourd'hui OU avant (retard)
    arrivees_prevues = Reservation.objects.filter(
        statut__in=['confirmee', 'en_attente'],
        date_arrivee__lte=today
    ).order_by('date_arrivee')

    # Liste des séjours en cours (pour Check-out et Services)
    sejours_en_cours = Reservation.objects.filter(statut='en_cours').order_by('date_depart')
    
    # Historique (Terminées ou Annulées) + En cours (pour consultation)
    # Pour l'onglet Réservations : En attente (toutes) + Confirmées (Futures uniquement, les autres sont dans Check-in)
    reservations_futures = Reservation.objects.filter(
        Q(statut='en_attente') | 
        (Q(statut='confirmee') & Q(date_arrivee__gt=today))
    ).order_by('date_arrivee')

    historique = Reservation.objects.filter(
        statut__in=['terminee', 'annulee', 'en_cours']
    ).order_by('-date_modification')[:100]
    
    # Listes pour les formulaires
    clients = Client.objects.all().order_by('nom')
    chambres_dispo_list = Chambre.objects.filter(statut='disponible').order_by('numero')
    
    # Données pour les Services (Consommations)
    boissons = BoissonBar.objects.filter(disponible=True).order_by('nom')
    plats = PlatMenu.objects.filter(disponible=True).order_by('categorie__ordre', 'nom')
    espaces = EspaceEvenementiel.objects.filter(statut='disponible').order_by('nom')

    # ── Revenus chambres du jour (check-outs effectués) ──
    from django.utils import timezone as tz
    aujourd_hui = tz.now().date()
    res_terminees_jour = Reservation.objects.filter(
        statut='terminee',
        date_modification__date=aujourd_hui
    )
    revenus_chambres = sum(r.get_total_general() for r in res_terminees_jour)
    revenus_total    = revenus_chambres

    # ── Activité récente ──
    activite_recente = []
    for res in Reservation.objects.filter(
        statut__in=['en_cours', 'terminee']
    ).order_by('-date_modification')[:8]:
        if res.statut == 'en_cours':
            activite_recente.append({
                'type': 'checkin',
                'heure': res.date_modification.strftime('%H:%M'),
                'texte': f"Check-in {res.client.nom_complet} — ch. {res.chambre.numero}"
            })
        else:
            activite_recente.append({
                'type': 'checkout',
                'heure': res.date_modification.strftime('%H:%M'),
                'texte': f"Check-out {res.client.nom_complet} — ch. {res.chambre.numero}"
            })

    # Réceptionnistes et serveurs
    from django.contrib.auth.models import User as AuthUser, Group
    receptionnistes = AuthUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
    try:
        grp_serveurs = Group.objects.get(name='Serveuse/Serveur')
        serveurs_restaurant = AuthUser.objects.filter(groups=grp_serveurs, is_active=True).order_by('first_name', 'last_name')
    except Group.DoesNotExist:
        serveurs_restaurant = AuthUser.objects.none()

    context = {
        'total_chambres': total_chambres,
        'chambres_disponibles': chambres_disponibles,
        'chambres_occupees': chambres_occupees,
        'chambres_maintenance': chambres_maintenance,
        'chambres_reservees': chambres_reservees,
        'chambres': chambres,
        'reservations_attente': reservations_attente,
        'reservations_confirmees': reservations_confirmees,
        'reservations_futures': reservations_futures,
        'arrivees_prevues': arrivees_prevues,
        'sejours_en_cours': sejours_en_cours,
        'historique': historique,
        'clients': clients,
        'chambres_dispo_list': chambres_dispo_list,
        'today': today,
        'boissons': boissons,
        'plats': plats,
        'espaces': espaces,
        'revenus_chambres': int(revenus_chambres),
        'revenus_total': int(revenus_total),
        'activite_recente': activite_recente,
        'receptionnistes': receptionnistes,
        'serveurs_restaurant': serveurs_restaurant,
    }
    
    return render(request, 'hotel/index.html', context)

@require_module_access('hotel')
def chambre_detail(request, chambre_id):
    """Détails d'une chambre"""
    chambre = get_object_or_404(Chambre, id=chambre_id)
    context = {'chambre': chambre}
    return render(request, 'hotel/chambre_detail.html', context)

@require_module_access('hotel')
@transaction.atomic
def checkin_reservation(request, reservation_id):
    """Effectuer le check-in d'une réservation existante avec mise à jour des infos client"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == 'POST':
        # Mise à jour des informations du client
        client = reservation.client
        
        # Récupération des données du formulaire
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        date_naissance = request.POST.get('date_naissance')
        nationalite = request.POST.get('nationalite')
        adresse = request.POST.get('adresse')
        ville = request.POST.get('ville')
        pays = request.POST.get('pays')
        telephone = request.POST.get('telephone')
        email = request.POST.get('email')
        piece_identite = request.POST.get('piece_identite')
        numero_piece = request.POST.get('numero_piece')
        
        # Mise à jour infos voyage
        reservation.nombre_adultes = request.POST.get('nombre_adultes', reservation.nombre_adultes)
        reservation.nombre_enfants = request.POST.get('nombre_enfants', reservation.nombre_enfants)
        reservation.provenance = request.POST.get('provenance', reservation.provenance)
        reservation.destination = request.POST.get('destination', reservation.destination)
        
        # Mise à jour Client
        updated = False
        if nom: client.nom = nom; updated=True
        if prenom: client.prenom = prenom; updated=True
        if date_naissance: client.date_naissance = date_naissance; updated=True
        if nationalite: client.nationalite = nationalite; updated=True
        if adresse: client.adresse = adresse; updated=True
        if ville: client.ville = ville; updated=True
        if pays: client.pays = pays; updated=True
        if telephone: client.telephone = telephone; updated=True
        if email: client.email = email; updated=True
        if piece_identite: client.piece_identite = piece_identite; updated=True
        if numero_piece: client.numero_piece = numero_piece; updated=True
        
        if updated:
            client.save()
            
        # Mise à jour statut réservation
        reservation.statut = 'en_cours'
        reservation.save()
        
        # Mise à jour chambre
        chambre = reservation.chambre
        chambre.statut = 'occupee'
        chambre.save()
        
        messages.success(request, f"Check-in effectué pour {client.nom_complet} — Chambre {chambre.numero}.")
        if request.POST.get('action') == 'print_form':
            return redirect('hotel:print_checkin_form', reservation_id=reservation.id)
        return redirect(reverse('hotel:index') + '?tab=checkinout')
    
    # Comportement GET standard (fallback ou lien direct)
    if reservation.statut != 'confirmee':
        messages.error(request, "Seule une réservation confirmée peut faire l'objet d'un check-in.")
        return redirect('hotel:index')
    
    # Si GET direct, on fait le check-in simple (comportement précédent)
    # Mais idéalement on devrait rediriger vers la modale via JS, mais ici c'est du backend.
    # On garde le comportement simple pour la rétrocompatibilité si JS échoue, 
    # mais l'UI principale utilisera le POST.
    reservation.statut = 'en_cours'
    reservation.save()
    reservation.chambre.statut = 'occupee'
    reservation.chambre.save()
    messages.success(request, f"Check-in effectué pour {reservation.client.nom_complet}.")
    return redirect(reverse('hotel:index') + '?tab=checkinout')

@require_module_access('hotel')
@transaction.atomic
def checkin_direct(request):
    """Créer un client, une réservation et faire le check-in directement"""
    if request.method == 'POST':
        # Données Client
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        
        # Données Réservation
        chambre_id = request.POST.get('chambre_id')
        date_depart = request.POST.get('date_depart')
        avance = Decimal(request.POST.get('avance', 0))
        
        # Infos complètes (ajoutées)
        date_naissance = request.POST.get('date_naissance')
        nationalite = request.POST.get('nationalite')
        adresse = request.POST.get('adresse', '').strip() or None
        ville = request.POST.get('ville', '').strip() or None
        pays = request.POST.get('pays', '').strip() or None
        email = request.POST.get('email', '').strip() or None
        piece_identite = request.POST.get('piece_identite', '').strip() or None
        numero_piece = request.POST.get('numero_piece', '').strip() or None
        nombre_adultes = request.POST.get('nombre_adultes', 1) or 1
        nombre_enfants = request.POST.get('nombre_enfants', 0) or 0
        provenance = request.POST.get('provenance', '').strip() or None
        destination = request.POST.get('destination', '').strip() or None

        # Nettoyage des champs date — éviter les valeurs vides
        date_naissance = (date_naissance or '').strip() or None

        if not all([nom, chambre_id, date_depart]):
            msg = "Veuillez remplir tous les champs obligatoires (Nom, Chambre, Date de départ)."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')
            
        # Création ou Récupération Client
        client_id = request.POST.get('client_id')
        client = None
        created = False
        
        if client_id and client_id != 'new':
             try:
                 client = Client.objects.get(id=client_id)
             except Client.DoesNotExist:
                 pass
        
        if not client:
             # Tentative de récupération par téléphone
             existing_clients = Client.objects.filter(telephone=telephone)
             if existing_clients.exists():
                 client = existing_clients.first()
             else:
                 client = Client.objects.create(
                    telephone=telephone,
                    nom=nom, 
                    prenom=prenom,
                    date_naissance=date_naissance,
                    nationalite=nationalite,
                    adresse=adresse,
                    ville=ville,
                    pays=pays,
                    email=email,
                    piece_identite=piece_identite,
                    numero_piece=numero_piece
                 )
                 created = True
        
        # Si le client existait, on met à jour ses infos si fournies
        if not created:
            client.nom = nom
            client.prenom = prenom
            if date_naissance: client.date_naissance = date_naissance
            if nationalite: client.nationalite = nationalite
            if adresse: client.adresse = adresse
            if ville: client.ville = ville
            if pays: client.pays = pays
            if email: client.email = email
            if piece_identite: client.piece_identite = piece_identite
            if numero_piece: client.numero_piece = numero_piece
            client.save()

        chambre = get_object_or_404(Chambre, id=chambre_id)
        
        # 1. Validation Statut Actuel
        if chambre.statut == 'maintenance':
            msg = f"La chambre {chambre.numero} est en maintenance et indisponible."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')
        elif chambre.statut == 'occupee':
            msg = f"La chambre {chambre.numero} est actuellement occupée. Sélectionnez une autre chambre."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')
        elif chambre.statut not in ['disponible', 'reservation']:
            msg = f"La chambre {chambre.numero} n'est pas disponible (Statut: {chambre.get_statut_display()})."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')

        # Préparation des dates pour vérification chevauchement
        today = timezone.now().date()
        try:
            date_depart_obj = timezone.datetime.strptime(date_depart, '%Y-%m-%d').date()
        except ValueError:
            msg = "Format de date invalide. Utilisez le format JJ/MM/AAAA."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')
            
        if date_depart_obj <= today:
            msg = "La date de départ doit être ultérieure à aujourd'hui."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')

        # 2. Validation Chevauchement Réservations Futures
        overlapping = Reservation.objects.filter(
            chambre=chambre,
            statut__in=['en_attente', 'confirmee', 'en_cours']
        ).filter(
            Q(date_arrivee__lt=date_depart_obj) & Q(date_depart__gt=today)
        )

        if overlapping.exists():
            if overlapping.filter(statut='en_cours').exists():
                msg = f"La chambre {chambre.numero} est occupée durant cette période. Choisissez d'autres dates ou une autre chambre."
            else:
                o = overlapping.first()
                msg = f"La chambre {chambre.numero} est déjà réservée du {o.date_arrivee.strftime('%d/%m/%Y')} au {o.date_depart.strftime('%d/%m/%Y')}. Choisissez d'autres dates."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect(reverse('hotel:index') + '?tab=checkinout')

        # Création Réservation
        duree = (date_depart_obj - today).days
        if duree < 1: duree = 1
        
        prix_total = duree * chambre.prix_nuit
        
        reservation = Reservation.objects.create(
            client=client,
            chambre=chambre,
            date_arrivee=today,
            date_depart=date_depart_obj,
            nombre_adultes=nombre_adultes,
            nombre_enfants=nombre_enfants,
            prix_total=prix_total,
            avance=avance,
            provenance=provenance,
            destination=destination,
            statut='en_cours' # Directement en cours
        )
        
        # Mise à jour Chambre
        chambre.statut = 'occupee'
        chambre.save()

        messages.success(request, f"Check-in direct effectué pour {client.nom_complet} — Chambre {chambre.numero}.")
        if request.POST.get('action') == 'print_form':
            return redirect('hotel:print_checkin_form', reservation_id=reservation.id)
        return redirect(reverse('hotel:index') + '?tab=checkinout')
        
    return redirect('hotel:index')

@require_module_access('hotel')
@transaction.atomic
def reservation_create(request):
    """Créer une nouvelle réservation"""
    if request.method == 'POST':
        # Client
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        
        # Réservation
        chambre_id = request.POST.get('chambre_id')
        date_arrivee = request.POST.get('date_arrivee')
        date_depart = request.POST.get('date_depart')
        avance = Decimal(request.POST.get('avance', 0))
        client_id = request.POST.get('client_id')
        
        # Validation Champs Obligatoires
        required_fields = [chambre_id, date_arrivee, date_depart]
        if not client_id or client_id == 'new':
             required_fields.append(nom)
             
        if not all(required_fields):
            msg = "Veuillez remplir les champs obligatoires (Client, Chambre, Dates)."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')
            
        # Validation Dates
        d_arrivee = timezone.datetime.strptime(date_arrivee, '%Y-%m-%d').date()
        d_depart = timezone.datetime.strptime(date_depart, '%Y-%m-%d').date()
        
        if d_arrivee >= d_depart:
            msg = "La date de départ doit être après la date d'arrivée."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')
            
        chambre = get_object_or_404(Chambre, id=chambre_id)
        if chambre.statut == 'maintenance':
            msg = f"La chambre {chambre.numero} est en maintenance. Choisissez une autre chambre."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')
        elif chambre.statut == 'occupee':
            msg = f"La chambre {chambre.numero} est actuellement occupée. Choisissez une autre chambre."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')

        # Validation Disponibilité (Chevauchement)
        # On vérifie s'il existe une réservation pour cette chambre qui chevauche la période demandée
        # (StartA < EndB) and (EndA > StartB)
        overlapping = Reservation.objects.filter(
            chambre_id=chambre_id,
            statut__in=['en_attente', 'confirmee', 'en_cours']
        ).filter(
            Q(date_arrivee__lt=d_depart) & Q(date_depart__gt=d_arrivee)
        )
        
        if overlapping.exists():
            if overlapping.filter(statut='en_cours').exists():
                msg = f"La chambre {chambre.numero} est occupée pour cette période. Choisissez d'autres dates ou une autre chambre."
            else:
                o = overlapping.first()
                msg = f"La chambre {chambre.numero} est déjà réservée du {o.date_arrivee.strftime('%d/%m/%Y')} au {o.date_depart.strftime('%d/%m/%Y')}. Choisissez d'autres dates."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': msg})
            messages.error(request, msg)
            return redirect('hotel:index')

        # Client (Get or Create)
        client_id = request.POST.get('client_id')
        client = None
        
        if client_id and client_id != 'new':
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                pass
                
        if not client:
            # Tentative de récupération par téléphone
            existing_clients = Client.objects.filter(telephone=telephone)
            if existing_clients.exists():
                client = existing_clients.first()
            else:
                client = Client.objects.create(
                    telephone=telephone,
                    nom=nom,
                    prenom=prenom
                )
        
        # Calcul Prix
        duree = (d_depart - d_arrivee).days
        prix_total = duree * chambre.prix_nuit
        
        statut = 'confirmee' if avance > 0 else 'en_attente'
        
        Reservation.objects.create(
            client=client,
            chambre=chambre,
            date_arrivee=d_arrivee,
            date_depart=d_depart,
            prix_total=prix_total,
            avance=avance,
            statut=statut
        )
        
        # Note: On ne change PAS le statut de la chambre ici.
        # La chambre reste 'disponible' jusqu'au check-in, sauf si c'est pour aujourd'hui
        # (géré par l'auto-correction dans hotel_index)
        
        messages.success(request, f"Réservation confirmée pour {client.nom_complet} — Ch. {chambre.numero} du {d_arrivee.strftime('%d/%m/%Y')} au {d_depart.strftime('%d/%m/%Y')}.")
        return redirect('hotel:index')
        
    return redirect('hotel:index')

@require_module_access('hotel')
def print_checkin_form(request, reservation_id):
    """Afficher la fiche de police pour impression"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'hotel/checkin_form_pdf.html', {'reservation': reservation})

from facturation.models import Ticket, Client as FacturationClient

@require_module_access('hotel')
@transaction.atomic
def checkout_reservation(request, reservation_id):
    """Effectuer le check-out d'une réservation avec facturation des services"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == 'POST':
        # Recalculer le prix total basé sur la durée réelle
        # ... logique existante de recalcul ...
        # (Cette partie reste inchangée si je ne la modifie pas ici, mais je dois m'assurer de ne pas casser le code existant)
        # Comme je remplace tout le bloc, je dois inclure la logique de recalcul.
        
        # 1. Mise à jour de la date de départ et du prix si nécessaire
        reservation.date_depart = timezone.now().date()
        
        # Recalcul du prix hébergement
        diff_time = abs(reservation.date_depart - reservation.date_arrivee)
        diff_days = diff_time.days or 1 # Minimum 1 jour
        
        nouveau_prix_total = 0
        if reservation.type_sejour == 'long_sejour':
            nouveau_prix_total = (reservation.chambre.prix_sejour or 0) * diff_days
        else:
            nouveau_prix_total = (reservation.chambre.prix_nuit or 0) * diff_days
            
        if nouveau_prix_total != reservation.prix_total:
            reservation.prix_total = nouveau_prix_total
            reservation.save()
            
        montant_paye = Decimal(request.POST.get('montant_encaisse', 0))
        reste_a_payer = reservation.get_montant_restant()
        
        if montant_paye < reste_a_payer:
            messages.error(request, "Le montant encaissé est inférieur au reste à payer.")
            return redirect(reverse('hotel:index') + '?tab=checkinout')
            
        # 2. Synchronisation du Client (Hotel -> Facturation)
        f_client = None
        if reservation.client:
            # Recherche par téléphone ou création
            f_client, created = FacturationClient.objects.get_or_create(
                telephone=reservation.client.telephone,
                defaults={
                    'nom': reservation.client.nom,
                    'prenom': reservation.client.prenom,
                    'email': reservation.client.email or '',
                    'adresse': reservation.client.adresse or ''
                }
            )
            # Mise à jour si existant (optionnel mais recommandé pour avoir les infos à jour)
            if not created:
                f_client.nom = reservation.client.nom
                f_client.prenom = reservation.client.prenom
                f_client.save()

        # 3. Génération du contenu du ticket (Format HTML pour impression thermique)
        # On construit une structure de table simple qui sera stylisée par le CSS du ticket
        
        # Lignes de services
        services_html = ""
        services = reservation.consommations.all()
        
        # Hébergement
        services_html += f"""
        <div class="row">
            <span class="item-name">Hébergement ({diff_days}j)</span>
            <span class="item-price">{reservation.get_prix_reel():,.0f} F</span>
        </div>
        """
        
        if services.exists():
            services_html += '<div class="row" style="margin: 5px 0; font-style: italic; border-bottom: none;">--- Services ---</div>'
            for s in services:
                prefix = s.get_type_service_display()
                services_html += f"""
                <div class="row">
                    <span class="item-name">[{prefix}] {s.nom} x{s.quantite}</span>
                    <span class="item-price">{s.total:,.0f} F</span>
                </div>
                """
        
        # Ajout du récapitulatif financier dans le contenu
        montant_avance = reservation.avance
        montant_total_general = reservation.get_total_general()
        montant_reste = montant_total_general - montant_avance
        
        services_html += '<div style="margin-top: 10px; border-top: 1px dashed #000; padding-top: 5px;">'
        
        if montant_avance > 0:
             services_html += f"""
            <div class="row">
                <span class="item-name">Total Général</span>
                <span class="item-price">{montant_total_general:,.0f} F</span>
            </div>
            <div class="row">
                <span class="item-name">Avance reçue</span>
                <span class="item-price">-{montant_avance:,.0f} F</span>
            </div>
            <div class="row bold">
                <span class="item-name">Reste à payer</span>
                <span class="item-price">{montant_reste:,.0f} F</span>
            </div>
            """

        services_html += '</div>'
        
        contenu = services_html
        
        # 4. Créer la ligne de paiement (Ticket)
        # Note: On ne change pas encore le statut de la réservation. 
        # La validation finale se fait après impression du ticket.
        
        mode_paiement = request.POST.get('mode_paiement', 'especes')
        if mode_paiement == 'mobile_money':
            operateur = request.POST.get('operateur_momo')
            if operateur:
                mode_paiement = operateur

        # Réceptionniste (depuis le champ readonly du formulaire) et Serveur
        receptionniste_nom = request.POST.get('serveur', '').strip() or request.user.get_full_name() or request.user.username
        serveur_nom = request.POST.get('serveur_resto', '').strip()
        if not serveur_nom:
            messages.error(request, "Veuillez sélectionner un serveur/serveuse avant de valider le check-out.")
            return redirect(reverse('hotel:index') + '?tab=checkinout')

        ticket = Ticket.objects.create(
            numero=generate_ticket_numero(),
            module='hotel',
            objet_id=reservation.id,
            client=f_client,
            montant_total=reservation.get_total_general(),
            montant_paye=montant_paye + reservation.avance,
            mode_paiement=mode_paiement,
            cree_par=request.user,
            contenu=contenu
        )

        messages.success(request, "Paiement enregistré. Veuillez imprimer le ticket pour clôturer le séjour.")
        request.session[f'ticket_{ticket.id}_serveur'] = serveur_nom
        request.session[f'ticket_{ticket.id}_receptionniste'] = receptionniste_nom
        return redirect('hotel:ticket_print', ticket_id=ticket.id)
        
    return redirect(reverse('hotel:index') + '?tab=historique')

@require_module_access('hotel')
def ticket_print(request, ticket_id):
    """Afficher le ticket pour impression"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    serveur = request.session.get(f'ticket_{ticket_id}_serveur', '')
    receptionniste = request.session.get(f'ticket_{ticket_id}_receptionniste', '')
    return render(request, 'facturation/ticket_print_thermal.html', {
        'ticket': ticket,
        'serveur': serveur,
        'receptionniste': receptionniste,
    })

@require_module_access('hotel')
@transaction.atomic
def finalize_checkout(request, ticket_id):
    """Finaliser le check-out (libérer la chambre) après impression"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # On vérifie si c'est bien un ticket d'hôtel
    if ticket.module != 'hotel':
        return JsonResponse({'status': 'error', 'message': 'Ticket invalide'}, status=400)
        
    try:
        if not ticket.objet_id:
             return JsonResponse({'status': 'error', 'message': 'Ticket sans réservation associée'}, status=400)

        reservation = Reservation.objects.get(id=ticket.objet_id)
        
        # Si déjà terminée, on ne fait rien mais on met à jour le ticket
        if reservation.statut == 'terminee':
            # Assurer que le ticket est marqué imprimé
            if not ticket.imprime:
                ticket.imprime = True
                ticket.date_impression = timezone.now()
                ticket.save()
            return JsonResponse({'status': 'success', 'message': 'Déjà clôturé'})
            
        # Mise à jour statuts
        reservation.statut = 'terminee'
        reservation.save()
        
        # Libérer la chambre
        if reservation.chambre:
            reservation.chambre.statut = 'disponible'
            reservation.chambre.save()
        
        # Marquer le ticket comme imprimé
        ticket.imprime = True
        ticket.date_impression = timezone.now()
        ticket.save()
        
        return JsonResponse({'status': 'success', 'message': 'Séjour clôturé avec succès'})
        
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Réservation introuvable'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Erreur serveur: {str(e)}'}, status=500)


@require_module_access('hotel')
@transaction.atomic
def ajouter_consommation(request, reservation_id):
    """Ajouter un service/consommation à une réservation"""
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        type_service = request.POST.get('type_service')
        quantite = int(request.POST.get('quantite', 1))
        
        conso = Consommation(reservation=reservation, type_service=type_service, quantite=quantite)
        
        try:
            if type_service == 'bar':
                boisson_id = request.POST.get('boisson_id')
                boisson = get_object_or_404(BoissonBar, id=boisson_id)
                if boisson.quantite_stock < quantite:
                    messages.error(request, f"Stock insuffisant pour {boisson.nom} (Reste: {boisson.quantite_stock})")
                    return redirect(f"{reverse('hotel:index')}?tab=checkinout")
                
                conso.boisson = boisson
                conso.nom = boisson.nom
                conso.prix_unitaire = boisson.prix
                
            elif type_service == 'restaurant':
                plat_id = request.POST.get('plat_id')
                plat = get_object_or_404(PlatMenu, id=plat_id)
                conso.plat = plat
                conso.nom = plat.nom
                conso.prix_unitaire = plat.prix
                
            elif type_service == 'espace':
                espace_id = request.POST.get('espace_id')
                espace = get_object_or_404(EspaceEvenementiel, id=espace_id)
                conso.espace = espace
                conso.nom = espace.nom
                conso.prix_unitaire = espace.prix_heure # Facturation à l'heure par défaut
                
            elif type_service == 'autre':
                conso.nom = request.POST.get('description')
                conso.prix_unitaire = Decimal(request.POST.get('prix'))
                
            conso.save() # Déclenche la gestion du stock via save() du modèle
            messages.success(request, "Service ajouté avec succès.")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du service: {str(e)}")
        
    return redirect(f"{reverse('hotel:index')}?tab=checkinout")


@require_module_access('hotel')
def api_consommations_reservation(request, reservation_id):
    """Liste toutes les consommations d'une réservation pour l'onglet En cours."""
    from .models import Reservation, Consommation
    reservation = get_object_or_404(Reservation, id=reservation_id)
    data = []
    for c in reservation.consommations.all().order_by('-date_ajout'):
        data.append({
            'id': c.id,
            'nom': c.nom,
            'type': c.type_service,
            'type_label': c.get_type_service_display(),
            'quantite': c.quantite,
            'prix': float(c.prix_unitaire),
            'total': float(c.total),
        })
    return JsonResponse({'consommations': data})


@require_module_access('hotel')
@require_POST
def api_modifier_consommation(request, conso_id):
    """Modifier la quantité d'une consommation hôtel."""
    from .models import Consommation
    try:
        conso = get_object_or_404(Consommation, id=conso_id)
        data = json.loads(request.body)
        new_qty = int(data.get('quantite', 1))
        if new_qty < 1:
            return JsonResponse({'success': False, 'error': 'Quantité invalide'})
        conso.quantite = new_qty
        conso.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('hotel')
@require_POST
def api_supprimer_consommation(request, conso_id):
    """Supprimer une consommation hôtel."""
    from .models import Consommation
    try:
        conso = get_object_or_404(Consommation, id=conso_id)
        conso.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
