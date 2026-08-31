import logging
from utils.permissions import require_module_access, require_kds_access
from django.shortcuts import render, redirect, get_object_or_404

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.template.loader import render_to_string
from django.db.models import Sum, Q
from django.utils import timezone
import json
from .models import Table, CategorieMenu, PlatMenu, Commande, LigneCommande, Reservation
from decimal import Decimal
from django.contrib.auth.models import User as AuthUser
from bar.models import BoissonBar, MouvementStockBar
from facturation.models import Ticket, generate_ticket_numero
from hotel.models import Client as HotelClient

from cuisine.utils import check_stock_availability, process_stock_movement
from cuisine.models import Ingredient
from .views_extension import create_reservation, update_reservation_status

@require_module_access('restaurant')
def restaurant_index(request):
    """Vue principale du restaurant"""
    
    # Boissons Bar : plus synchronisées automatiquement vers le restaurant.
    # Elles sont vendues via le TPE Cave. Pour les forfaits (ex: piscine),
    # utiliser le système de Forfaits (voir restaurant/models.py → Forfait).

    # Récupérer toutes les catégories et plats
    # Plats avec fiche technique OU plats simples (sans stock)
    from cuisine.models import Plat as PlatCuisine
    from django.db.models import Q
    _plats_avec_ft = PlatCuisine.objects.filter(
        fiche_technique__isnull=False
    ).values_list('pk', flat=True)
    categories = CategorieMenu.objects.all()
    plats = PlatMenu.objects.filter(
        disponible=True
    ).filter(
        Q(cuisine_plat_id__in=_plats_avec_ft) | Q(is_simple=True)
    )
    
    # Commandes en cours (Non payées)
    commandes_en_cours_list = Commande.objects.filter(statut__in=['en_attente', 'en_preparation', 'prete', 'servie']).order_by('-date_modification')
    commandes_en_cours = commandes_en_cours_list.count()
    
    # Tables — tri numérique (SBT1, SBT2 … SBT10, SBT11)
    from django.db.models.expressions import RawSQL
    tables = Table.objects.annotate(
        num=RawSQL("CAST(REGEXP_REPLACE(numero, '[^0-9]', '', 'g') AS INTEGER)", [])
    ).order_by('num', 'numero')

    # Réservations actives
    reservations = Reservation.objects.filter(
        statut='confirmee',
        date_reservation__gte=timezone.now()
    ).order_by('date_reservation')
    
    # Vérification du stock pour chaque plat
    for plat in plats:
        if plat.is_simple:
            plat.en_stock = True
            plat.stock_quantity = 999
            continue
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available

        ft = plat.fiche_technique
        if ft is not None and ft.lignes.exists():
            plat.stock_quantity = ft.max_portions_possibles()
        else:
            # FT vide ou absente → quantité via ingrédient homonyme
            try:
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                plat.stock_quantity = int(ing.quantite_stock) if ing else 999
            except Exception:
                plat.stock_quantity = 999
        
    # Accompagnements — extraits de la liste déjà évaluée pour conserver en_stock/stock_quantity
    accompagnements = [p for p in plats if p.is_accompagnement]

    context = {
        'categories': categories,
        'plats': plats,
        'accompagnements': accompagnements,
        'commandes_en_cours': commandes_en_cours,
        'commandes_en_cours_list': commandes_en_cours_list, # Ajouté pour l'onglet
        'tables': tables,
        'reservations': reservations,
    }
    
    return render(request, 'restaurant/index.html', context)

def _map_mode_paiement(mode, operateur=''):
    """Mappe le code TPE vers le code Ticket (PAIEMENT_CHOICES facturation)."""
    if mode == 'mobile':
        op = (operateur or '').lower()
        if 'wave' in op:       return 'wave'
        if 'orange' in op:     return 'orange_money'
        if 'mtn' in op:        return 'mtn_money'
        if 'moov' in op:       return 'moov_money'
        return 'mobile_money'
    if mode == 'carte':   return 'carte_bancaire'
    if mode == 'chambre': return 'autre'
    return mode  # 'especes'


@require_module_access('restaurant')
@require_POST
def valider_commande(request):
    """Valide une commande (Paiement uniquement maintenant, l'ajout se fait en temps réel)"""
    try:
        data = json.loads(request.body)
        commande_id = data.get('commande_id')
        action = data.get('action', 'paiement')
        montant_encaisse = Decimal(str(data.get('montant_encaisse', 0)))
        montant_especes  = Decimal(str(data.get('montant_especes', 0) or 0))
        client_name = data.get('client', '')

        if not commande_id:
            return JsonResponse({'success': False, 'message': 'ID Commande manquant'})
            
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Mise à jour infos client si fourni
        if client_name:
            commande.nom_client = client_name
            commande.save()

        if action == 'paiement':
            # Calculer le total depuis les lignes (le champ total DB peut être 0)
            total_lignes = sum(l.get_total() for l in commande.lignes.all())
            if total_lignes > 0:
                commande.total = total_lignes
                commande.save(update_fields=['total'])
            if commande.total <= 0:
                return JsonResponse({'success': False, 'message': 'Le total est nul.'})

            serveur_nom = data.get('serveur', '')
            if not serveur_nom:
                return JsonResponse({'success': False, 'message': 'Veuillez sélectionner un serveur avant de valider.'})

            # Frais salon privé (heures saisies manuellement par la caissière)
            frais_salon = Decimal('0')
            heures_salon = int(data.get('heures_salon', 0) or 0)
            tarif_salon = Decimal('0')
            if heures_salon > 0 and commande.table_id:
                table_obj = commande.table
                if getattr(table_obj, 'est_salon_prive', False):
                    tarif_salon = table_obj.tarif_horaire
                    frais_salon = Decimal(str(heures_salon)) * tarif_salon

            with transaction.atomic():
                commande.statut = 'payee'
                # Caissier = utilisateur connecté
                commande.caissier = request.user
                # Montant rendu
                total_net = commande.total_net
                commande.montant_rendu = max(Decimal('0'), montant_encaisse - Decimal(str(total_net)) - frais_salon)
                # Sauvegarder le serveur sélectionné dans la commande
                if serveur_nom:
                    from django.contrib.auth.models import User as AuthUser
                    srv = AuthUser.objects.filter(
                        first_name__icontains=serveur_nom.split()[0] if serveur_nom else ''
                    ).first() or AuthUser.objects.filter(
                        username__icontains=serveur_nom.split()[0] if serveur_nom else ''
                    ).first()
                    if srv:
                        commande.serveur = srv
                commande.save()
                # Numérotation fiscale séquentielle
                commande.assigner_numero_fiscal()
                
                if commande.table:
                    commande.table.statut = 'disponible'
                    commande.table.save()
                
                # Génération Ticket
                numero_ticket = generate_ticket_numero()
                
                all_items_objs = LigneCommande.objects.filter(commande=commande).select_related('plat', 'accompagnement', 'boisson')
                
                # Génération du contenu HTML pour le Ticket
                services_html = '<span class="ticket-meta" data-serveur="' + serveur_nom + '"></span>'

                if client_name:
                    services_html += f"""
                    <div class="border-bottom" style="margin-bottom: 10px;">
                        <div class="row">
                            <span class="bold">Client:</span>
                            <span>{client_name}</span>
                        </div>
                    </div>
                    """

                for li in all_items_objs:
                    total_line = li.prix_unitaire * li.quantite
                    if li.plat:
                        nom_display = li.plat.nom
                        if li.accompagnement:
                            nom_display += f" + {li.accompagnement.nom}"
                    elif hasattr(li, 'boisson') and li.boisson:
                        nom_display = li.boisson.nom
                    elif li.nom_article:
                        nom_display = li.nom_article
                    else:
                        nom_display = "Article"

                    services_html += f"""
                    <div class="row">
                        <span class="item-name">{nom_display} x{li.quantite}</span>
                        <span class="item-price">{total_line:,.0f} F</span>
                    </div>
                    """

                # Ligne salon privé dans le contenu du ticket
                if frais_salon > 0:
                    services_html += f"""
                    <div class="row salon-prive">
                        <span class="item-name">Salon privé {heures_salon}h × {int(tarif_salon):,} F</span>
                        <span class="item-price">{int(frais_salon):,} F</span>
                    </div>
                    """

                montant_total_ticket = commande.total + frais_salon

                # Création du Ticket
                ticket = Ticket.objects.create(
                    numero=numero_ticket,
                    module='restaurant',
                    montant_total=montant_total_ticket,
                    client=None,
                    contenu=services_html,
                    objet_id=commande.id,
                    montant_paye=montant_encaisse,
                    mode_paiement=_map_mode_paiement(
                        data.get('mode_paiement', 'especes'),
                        data.get('operateur_mobile', ''),
                    ),
                    cree_par=request.user,
                    imprime=True
                )

                # Si mode chambre : lier les articles à la réservation hôtel
                reservation_hotel_id = data.get('reservation_hotel_id')
                mode_paiement_val = data.get('mode_paiement', 'especes')
                sur_chambre = data.get('sur_chambre', False)
                if mode_paiement_val == 'chambre' and reservation_hotel_id:
                    try:
                        from hotel.models import Reservation as HotelRes, Consommation as HotelConso
                        hotel_res = HotelRes.objects.get(id=reservation_hotel_id, statut='en_cours')
                        for li in all_items_objs:
                            nom_li = li.plat.nom if li.plat else (li.boisson.nom if hasattr(li,'boisson') and li.boisson else li.nom_article or 'Article')
                            HotelConso.objects.create(
                                reservation=hotel_res,
                                type_service='restaurant',
                                plat=li.plat if li.plat else None,
                                nom=f'[Restaurant] {nom_li}',
                                quantite=li.quantite,
                                prix_unitaire=li.prix_unitaire,
                            )
                    except Exception as e_chambre:
                        logger.warning(
                            "Impossible de lier la commande %s à la réservation hôtel %s : %s",
                            commande.id, reservation_hotel_id, e_chambre
                        )

                # Rendu ticket thermique avec serveur
                mode_short_map = {'wave':'WAVE','orange_money':'ORANGE','mtn_money':'MTN','especes':'ESP','carte_bancaire':'CARTE'}
                tp = ticket.mode_paiement or 'especes'
                montant_mobile = max(Decimal('0'), ticket.montant_total - montant_especes) if montant_especes > 0 else Decimal('0')
                ticket_html = render_to_string('facturation/ticket_print_thermal.html', {
                    'ticket':           ticket,
                    'serveur':          serveur_nom,
                    'is_original':      True,
                    'montant_especes':  montant_especes if montant_especes > 0 else None,
                    'montant_mobile':   montant_mobile  if montant_especes > 0 else None,
                    'mode_short':       mode_short_map.get(tp, tp.upper()),
                    'frais_salon':      frais_salon if frais_salon > 0 else None,
                    'heures_salon':     heures_salon if frais_salon > 0 else None,
                    'tarif_salon':      tarif_salon if frais_salon > 0 else None,
                })
                
                return JsonResponse({'success': True, 'ticket_html': ticket_html, 'action': 'paiement'})
        
        else:
            # Juste mise en attente (déjà fait par l'ajout temps réel, mais on peut mettre à jour le statut si besoin)
            # En temps réel, la commande est déjà créée.
            # On peut juste confirmer.
            return JsonResponse({'success': True, 'message': 'Commande mise en attente', 'action': 'mise_en_attente'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})

@require_module_access('restaurant')
@require_POST
def annuler_commande(request):
    """Annule une commande complète et restaure le stock"""
    try:
        data = json.loads(request.body)
        commande_id = data.get('commande_id')
        motif = data.get('motif', 'Annulation client')
        
        if not commande_id:
            return JsonResponse({'success': False, 'message': 'ID Commande manquant'})
            
        commande = get_object_or_404(Commande, id=commande_id)
        
        if commande.statut in ['payee', 'annulee']:
            return JsonResponse({'success': False, 'message': f'Impossible d\'annuler une commande {commande.get_statut_display()}'})
            
        with transaction.atomic():
            # 1. Restaurer le stock pour chaque ligne
            for ligne in commande.lignes.select_related('plat', 'accompagnement', 'boisson').all():
                process_stock_movement(
                    ligne.plat,
                    ligne.quantite,
                    'entree',
                    request.user,
                    f"Annulation Commande #{commande.id}"
                )
                if ligne.accompagnement:
                    process_stock_movement(
                        ligne.accompagnement,
                        ligne.quantite,
                        'entree',
                        request.user,
                        f"Annulation Accompagnement #{commande.id}"
                    )
                if ligne.boisson:
                    MouvementStockBar.objects.create(
                        boisson=ligne.boisson,
                        type_mouvement='entree',
                        quantite=ligne.quantite,
                        commentaire=f"Annulation Restaurant #{commande.id}",
                        utilisateur=request.user,
                    )
            
            # 2. Mettre à jour le statut
            commande.statut = 'annulee'
            commande.save()
            
            # 3. Libérer la table uniquement si plus aucune commande active
            table_freed = False
            if commande.table:
                autres_actives = Commande.objects.filter(
                    table=commande.table,
                    statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
                ).exclude(id=commande.id).exists()
                if not autres_actives:
                    commande.table.statut = 'disponible'
                    commande.table.save()
                    table_freed = True

        return JsonResponse({'success': True, 'message': 'Commande annulée avec succès', 'table_freed': table_freed})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_module_access('restaurant')
@require_POST
def add_accompagnement_to_ligne(request):
    """Ajoute ou modifie l'accompagnement d'une ligne existante"""
    try:
        data = json.loads(request.body)
        ligne_id = data.get('ligne_id')
        acc_id = data.get('accompagnement_id')
        
        if not ligne_id:
            return JsonResponse({'success': False, 'message': 'Ligne ID manquant'})
            
        ligne = get_object_or_404(LigneCommande, id=ligne_id)
        commande = ligne.commande
        
        # Nouvel accompagnement
        new_acc = get_object_or_404(PlatMenu, id=acc_id) if acc_id else None
        
        # Vérification stricte : le plat doit être marqué comme accompagnement par la cuisine
        if new_acc and not new_acc.is_accompagnement:
            return JsonResponse({'success': False, 'message': 'Ce plat n\'est pas défini comme accompagnement par la cuisine.'})
        
        with transaction.atomic():
            # 1. Gestion de l'ancien accompagnement (si existe)
            if ligne.accompagnement:
                # On restaure le stock de l'ancien
                process_stock_movement(
                    ligne.accompagnement, 
                    ligne.quantite, 
                    'entree', 
                    request.user, 
                    f"Modif Accompagnement (Retour) #{commande.id}"
                )
                # On déduit du prix total de la commande
                # Note: Le prix unitaire de la ligne inclut l'ancien acc.
                # On va recalculer proprement.
            
            # 2. Gestion du nouvel accompagnement
            if new_acc:
                # Check Stock
                is_available, err = check_stock_availability(new_acc, ligne.quantite)
                if not is_available:
                    # Si fail, on rollback tout (atomic)
                    raise Exception(err)
                
                # Déstockage
                process_stock_movement(
                    new_acc,
                    ligne.quantite,
                    'sortie',
                    request.user,
                    f"Modif Accompagnement (Sortie) #{commande.id}"
                )
            
            # 3. Mise à jour Ligne
            # Prix de base du plat (On suppose que prix_unitaire = plat + old_acc)
            # Pour être sûr, on reprend le prix du plat original
            prix_base_plat = ligne.plat.prix
            prix_new_acc = new_acc.prix if new_acc else 0
            
            new_prix_unitaire = prix_base_plat + prix_new_acc
            
            # Différence pour le total commande
            # Différence par unité * quantité
            diff_unitaire = new_prix_unitaire - ligne.prix_unitaire
            diff_total = diff_unitaire * ligne.quantite
            
            ligne.accompagnement = new_acc
            ligne.prix_unitaire = new_prix_unitaire
            ligne.save()
            
            commande.total = float(commande.total) + float(diff_total)
            commande.save()

        # Retour état
        items = []
        for l in commande.lignes.all().order_by('id'):
            nom_affiche = (l.get_nom if hasattr(l,"get_nom") else l.nom_article or (l.plat.nom if l.plat else (l.boisson.nom if hasattr(l,"boisson") and l.boisson else "?")))
            if l.accompagnement:
                nom_affiche += f" (+ {l.accompagnement.nom})"
            items.append({
                'id': l.id,
                'nom': nom_affiche,
                'prix': float(l.prix_unitaire),
                'quantite': l.quantite,
                'has_acc': bool(l.accompagnement),
                'plat_id': l.plat.id if l.plat else None
            })
            
        return JsonResponse({
            'success': True,
            'items': items,
            'total': float(commande.total)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_module_access('restaurant')
def recuperer_commande(request, commande_id):
    """Récupère les détails d'une commande en cours"""
    try:
        commande = Commande.objects.get(id=commande_id)
        items = []
        for ligne in commande.lignes.all().select_related('plat', 'accompagnement', 'boisson').order_by('id'):
            if hasattr(ligne, 'get_nom'):
                nom_affiche = ligne.get_nom
            elif ligne.nom_article:
                nom_affiche = ligne.nom_article
            elif ligne.plat:
                nom_affiche = ligne.plat.nom
                if ligne.accompagnement:
                    nom_affiche += f" (+ {ligne.accompagnement.nom})"
            elif hasattr(ligne, 'boisson') and ligne.boisson:
                nom_affiche = ligne.boisson.nom
            else:
                nom_affiche = "Article"

            items.append({
                'id':       ligne.id,
                'nom':      nom_affiche,
                'prix':     float(ligne.prix_unitaire),
                'quantite': ligne.quantite,
            })

        return JsonResponse({'success': True, 'commande': _serialize_commande(commande)})
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande introuvable'})

@require_module_access('restaurant')
@require_POST
def supprimer_ligne_commande(request):
    """Supprime une ligne de commande et restaure le stock"""
    try:
        data = json.loads(request.body)
        ligne_id = data.get('ligne_id')
        
        if not ligne_id:
            return JsonResponse({'success': False, 'message': 'ID de ligne manquant'})
            
        ligne = get_object_or_404(LigneCommande, id=ligne_id)
        commande = ligne.commande
        plat = ligne.plat
        quantite = ligne.quantite
        
        # Restauration Stock (Cuisine ou Cave)
        process_stock_movement(plat, quantite, 'entree', request.user, f"Annulation Restaurant - Commande #{commande.id}")
        if ligne.accompagnement:
            process_stock_movement(ligne.accompagnement, quantite, 'entree', request.user, f"Annulation Accompagnement - Commande #{commande.id}")

        # Suppression
        montant_ligne = ligne.prix_unitaire * quantite
        ligne.delete()
        
        # Mise à jour total commande
        commande.total = commande.total - montant_ligne
        if commande.total < 0: commande.total = Decimal('0')
        commande.save()
        
        # Si la commande est maintenant vide → annulation automatique + libération table
        commande_annulee = False
        if not commande.lignes.exists():
            commande.statut = 'annulee'
            commande.save()
            commande_annulee = True
            if commande.table:
                autres_actives = Commande.objects.filter(
                    table=commande.table,
                    statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
                ).exclude(id=commande.id).exists()
                if not autres_actives:
                    commande.table.statut = 'disponible'
                    commande.table.save()
            return JsonResponse({
                'success': True,
                'items': [],
                'total': 0,
                'commande_annulee': True,
            })

        data_out = _serialize_commande(commande)
        return JsonResponse({
            'success': True,
            'commande_annulee': False,
            **data_out,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_module_access('restaurant')
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
        
        from django.utils.dateparse import parse_datetime
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

@require_module_access('restaurant')
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
        
        # Si annulée -> Table Disponible (si elle était réservée)
        if new_status == 'annulee':
            if res.table.statut == 'reservee':
                res.table.statut = 'disponible'
                res.table.save()
        
        # Si terminée (Arrivé) -> Table Occupée + Création Commande
        elif new_status == 'terminee':
            res.table.statut = 'occupee'
            res.table.save()
            
            # Créer commande vide pour cette table si elle n'existe pas déjà
            existing_cmd = Commande.objects.filter(
                table=res.table, 
                statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
            ).first()
            
            if not existing_cmd:
                Commande.objects.create(
                    table=res.table,
                    nom_client=res.client_nom,
                    serveur=request.user,
                    statut='en_attente'
                )
                
        return JsonResponse({
            'success': True,
            'table_id': res.table.id,
            'table_numero': res.table.numero,
            'client_nom': res.client_nom
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def _resoudre_serveur(nom):
    """Retourne l'User correspondant au nom complet ou username, ou None."""
    if not nom:
        return None
    mots = nom.strip().split()
    qs = AuthUser.objects.filter(first_name__icontains=mots[0])
    if len(mots) > 1:
        qs = qs.filter(last_name__icontains=mots[-1])
    return qs.first() or AuthUser.objects.filter(username__icontains=mots[0]).first()


@require_module_access('restaurant')
@require_POST
def ajouter_item_commande(request):
    """Ajoute un item à la commande en temps réel (crée/incrémente ligne + déstocke)"""
    try:
        data = json.loads(request.body)
        table_id = data.get('table_id')
        commande_id = data.get('commande_id')
        nom_plat = data.get('nom')
        plat_id = data.get('plat_id')
        acc_id = data.get('accompagnement_id') # Nouvel ID pour l'accompagnement
        
        # 1. Gestion Commande / Table
        serveur_user = _resoudre_serveur(data.get('serveur', '')) or request.user
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
            # Mettre à jour le serveur si pas encore assigné correctement
            if commande.serveur == request.user and serveur_user != request.user:
                commande.serveur = serveur_user
                commande.save(update_fields=['serveur'])
        elif table_id:
            table = get_object_or_404(Table, id=table_id)
            commande = Commande.objects.filter(table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']).first()
            if not commande:
                commande = Commande.objects.create(
                    table=table,
                    serveur=serveur_user,
                    statut='en_attente',
                    nom_client=data.get('client', '')
                )
                table.statut = 'occupee'
                table.save()
        elif data.get('emporter'):
            commande = Commande.objects.create(
                table=None,
                serveur=serveur_user,
                statut='en_attente',
                nom_client=data.get('client', '') or 'À emporter',
            )
        else:
            return JsonResponse({'success': False, 'message': 'Table ou mode emporter requis'})

        # 2. Obtenir le Plat
        if plat_id:
            plat = get_object_or_404(PlatMenu, id=plat_id)
            nom_plat = plat.nom
        else:
            plat = get_object_or_404(PlatMenu, nom=nom_plat)
            
        # 2b. Obtenir l'Accompagnement (si présent)
        acc = None
        if acc_id:
            acc = get_object_or_404(PlatMenu, id=acc_id)
        
        # 3. Vérification Stock (Pour 1 unité)
        # Plat principal
        is_available, error_msg = check_stock_availability(plat, 1)
        if not is_available:
            return JsonResponse({'success': False, 'message': error_msg})
            
        # Accompagnement
        if acc:
            is_acc_available, acc_error = check_stock_availability(acc, 1)
            if not is_acc_available:
                return JsonResponse({'success': False, 'message': f"Accompagnement indisponible: {acc.nom}"})

        # 4. Transaction Atomique (Ajout + Déstockage)
        with transaction.atomic():
            # Chercher ligne existante pour ce couple (plat + accompagnement)
            # On doit matcher l'accompagnement aussi (None ou ID)
            ligne = LigneCommande.objects.filter(
                commande=commande, 
                plat=plat, 
                accompagnement=acc
            ).first()
            
            prix_total_unit = plat.prix + (acc.prix if acc else 0)
            
            if ligne:
                ligne.quantite += 1
                ligne.save()
            else:
                ligne = LigneCommande.objects.create(
                    commande=commande, 
                    plat=plat, 
                    accompagnement=acc,
                    quantite=1, 
                    prix_unitaire=prix_total_unit
                )
            
            # Déstockage Plat
            process_stock_movement(plat, 1, 'sortie', request.user, f"Ajout Restaurant #{commande.id}")
            
            # Déstockage Accompagnement
            if acc:
                process_stock_movement(acc, 1, 'sortie', request.user, f"Ajout Accompagnement #{commande.id}")
            
            # Mise à jour Total Commande
            commande.total = float(commande.total) + float(prix_total_unit)
            commande.save()
            
        # 5. Retourner l'état complet
        data_out = _serialize_commande(commande)
        return JsonResponse({'success': True, 'commande_id': commande.id, **data_out})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_module_access('restaurant')
@require_POST
def update_ligne_quantite(request):
    """Met à jour la quantité (+1 ou -1) avec gestion stock"""
    try:
        data = json.loads(request.body)
        ligne_id = data.get('ligne_id')
        delta = int(data.get('delta')) # 1 ou -1
        
        ligne = get_object_or_404(LigneCommande, id=ligne_id)
        plat = ligne.plat
        commande = ligne.commande
        
        with transaction.atomic():
            prix_unit = ligne.prix_unitaire
            boisson   = ligne.boisson  # peut être None (ligne cuisine)

            if delta > 0:
                # Ajout (+1)
                # Check stock Plat (cuisine)
                is_available, error_msg = check_stock_availability(plat, 1)
                if not is_available: return JsonResponse({'success': False, 'message': error_msg})

                # Check stock Boisson (bar)
                if boisson and boisson.est_en_rupture:
                    return JsonResponse({'success': False, 'message': f"{boisson.nom} : stock insuffisant"})

                # Check stock Accompagnement
                if ligne.accompagnement:
                     is_acc, acc_err = check_stock_availability(ligne.accompagnement, 1)
                     if not is_acc: return JsonResponse({'success': False, 'message': f"Accompagnement indisponible: {ligne.accompagnement.nom}"})

                # Update
                ligne.quantite += 1
                ligne.save()

                # Destock cuisine
                process_stock_movement(plat, 1, 'sortie', request.user, f"Ajout Restaurant #{commande.id}")
                if ligne.accompagnement:
                    process_stock_movement(ligne.accompagnement, 1, 'sortie', request.user, f"Ajout Accompagnement #{commande.id}")
                # Destock boisson bar
                if boisson:
                    boisson.destock(1, f"Ajout Restaurant #{commande.id}", request.user)

                commande.total = float(commande.total) + float(prix_unit)

            else:
                # Retrait (-1)
                if ligne.quantite > 1:
                    ligne.quantite -= 1
                    ligne.save()

                    # Restock cuisine
                    process_stock_movement(plat, 1, 'entree', request.user, f"Retrait Restaurant #{commande.id}")
                    if ligne.accompagnement:
                        process_stock_movement(ligne.accompagnement, 1, 'entree', request.user, f"Retrait Accompagnement #{commande.id}")
                    # Restock boisson bar
                    if boisson:
                        boisson.restock(1, f"Retrait Restaurant #{commande.id}", request.user)

                    commande.total = float(commande.total) - float(prix_unit)

                else:
                    # Suppression complète de la ligne
                    process_stock_movement(plat, 1, 'entree', request.user, f"Retrait Restaurant #{commande.id}")
                    if ligne.accompagnement:
                        process_stock_movement(ligne.accompagnement, 1, 'entree', request.user, f"Retrait Accompagnement #{commande.id}")
                    if boisson:
                        boisson.restock(1, f"Retrait Restaurant #{commande.id}", request.user)

                    ligne.delete()
                    commande.total = float(commande.total) - float(prix_unit)

            if commande.total < 0: commande.total = 0
            commande.save()

        # Retour état complet
        cmd = Commande.objects.get(id=commande.id)
        data_out = _serialize_commande(cmd)
        return JsonResponse({'success': True, **data_out})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def _serialize_commande(commande):
    """Helper — sérialise une Commande avec tous les champs Sprint1."""
    items = []
    for l in commande.lignes.all().select_related('plat', 'accompagnement', 'boisson').order_by('id'):
        nom = l.get_nom if hasattr(l, 'get_nom') else (l.nom_article or (l.plat.nom if l.plat else '?'))
        items.append({
            'id':       l.id,
            'nom':      nom,
            'prix':     float(l.prix_unitaire),
            'quantite': l.quantite,
            'note':     l.note or '',
            'plat_id':  l.plat.id if l.plat else None,
            'has_acc':  bool(l.accompagnement),
        })
    serveur_nom = ''
    if commande.serveur:
        serveur_nom = commande.serveur.get_full_name() or commande.serveur.username
    return {
        'id':          commande.id,
        'table_id':    commande.table.id if commande.table else None,
        'statut':      commande.statut,
        'total':       float(commande.total),
        'remise_pct':  float(commande.remise_pct),
        'total_net':   commande.total_net,
        'nb_couverts': commande.nb_couverts,
        'client':      commande.nom_client or '',
        'serveur':     serveur_nom,
        'items':       items,
    }


@require_module_access('restaurant')
@require_POST
def update_note_ligne(request):
    """Met à jour la note/instruction d'une ligne."""
    try:
        data    = json.loads(request.body)
        ligne   = get_object_or_404(LigneCommande, id=data['ligne_id'])
        ligne.note = (data.get('note') or '').strip()[:200]
        ligne.save(update_fields=['note'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
@require_POST
def set_remise_commande(request):
    """Applique une remise % sur la commande."""
    try:
        data       = json.loads(request.body)
        commande   = get_object_or_404(Commande, id=data['commande_id'])
        pct        = float(data.get('remise_pct', 0))
        pct        = max(0, min(100, pct))
        commande.remise_pct = pct
        commande.save(update_fields=['remise_pct'])
        return JsonResponse({'success': True, 'remise_pct': pct, 'total_net': commande.total_net})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
@require_POST
def update_couverts(request):
    """Met à jour le nombre de couverts de la commande."""
    try:
        data       = json.loads(request.body)
        commande   = get_object_or_404(Commande, id=data['commande_id'])
        nb         = max(1, int(data.get('nb_couverts', 1)))
        commande.nb_couverts = nb
        commande.save(update_fields=['nb_couverts'])
        return JsonResponse({'success': True, 'nb_couverts': nb})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_kds_access
def kds_view(request):
    """Écran KDS cuisine — liste des commandes actives."""
    return render(request, 'restaurant/kds.html', {})


def kds_salle_view(request):
    """Vue salle — lecture seule, protégée par PIN de session."""
    if not request.session.get('salle_unlocked'):
        return render(request, 'restaurant/kds_salle_pin.html', {})
    return render(request, 'restaurant/kds_salle.html', {})


def kds_salle_pin(request):
    """Vérifie le PIN salle et ouvre la session si correct."""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    from django.conf import settings
    pin_saisi = request.POST.get('pin', '').strip()
    if pin_saisi == getattr(settings, 'SALLE_PIN', '1234'):
        request.session['salle_unlocked'] = True
        request.session.set_expiry(86400 * 30)  # 30 jours
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'message': 'Code incorrect'}, status=403)


def kds_salle_marquer_servi(request):
    """Marque une commande 'prete' comme 'servie' — session PIN uniquement."""
    if not request.session.get('salle_unlocked'):
        return JsonResponse({'ok': False, 'message': 'Non autorisé'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    try:
        data = json.loads(request.body)
        commande = get_object_or_404(Commande, id=data['commande_id'], statut='prete')
        commande.statut = 'servie'
        commande.save(update_fields=['statut'])
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'message': str(e)}, status=400)


def kds_salle_api(request):
    """API salle lecture seule — protégée par PIN de session."""
    if not request.session.get('salle_unlocked'):
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    commandes = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete']
    ).prefetch_related(
        'lignes__plat', 'lignes__accompagnement', 'lignes__boisson'
    ).select_related('table', 'serveur').order_by('date_creation')

    result = []
    for cmd in commandes:
        lignes = [{'nom': l.get_nom, 'quantite': l.quantite} for l in cmd.lignes.all()]
        if cmd.serveur:
            serveur_nom = cmd.serveur.get_full_name() or cmd.serveur.username
        else:
            serveur_nom = ''
        result.append({
            'id': cmd.id,
            'table': cmd.table.numero if cmd.table else 'À emporter',
            'statut': cmd.statut,
            'nb_couverts': cmd.nb_couverts,
            'serveur': serveur_nom,
            'lignes': lignes,
            'age_min': int((timezone.now() - cmd.date_creation).total_seconds() // 60),
        })
    return JsonResponse({'commandes': result})


@require_kds_access
def kds_api(request):
    """API polling KDS — retourne les commandes en_attente et en_preparation."""
    commandes = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete']
    ).prefetch_related(
        'lignes__plat', 'lignes__accompagnement', 'lignes__boisson'
    ).select_related('table', 'serveur').order_by('date_creation')

    result = []
    for cmd in commandes:
        lignes = [{'nom': l.get_nom, 'quantite': l.quantite, 'note': l.note or ''} for l in cmd.lignes.all()]
        if cmd.serveur:
            serveur_nom = cmd.serveur.get_full_name() or cmd.serveur.username
        else:
            serveur_nom = ''
        result.append({
            'id': cmd.id,
            'table': cmd.table.numero if cmd.table else 'À emporter',
            'statut': cmd.statut,
            'nb_couverts': cmd.nb_couverts,
            'client': cmd.nom_client or '',
            'serveur': serveur_nom,
            'lignes': lignes,
            'age_min': int((timezone.now() - cmd.date_creation).total_seconds() // 60),
        })
    return JsonResponse({'commandes': result})


@require_kds_access
@require_POST
def kds_changer_statut(request):
    """Change le statut d'une commande depuis le KDS."""
    try:
        data = json.loads(request.body)
        commande = get_object_or_404(Commande, id=data['commande_id'])
        nouveau = data.get('statut')
        if nouveau not in ('en_preparation', 'prete', 'servie'):
            return JsonResponse({'success': False, 'message': 'Statut invalide'})
        commande.statut = nouveau
        commande.save(update_fields=['statut'])
        return JsonResponse({'success': True, 'statut': nouveau})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
@require_POST
def transferer_table(request):
    """Transfère une commande d'une table vers une autre."""
    try:
        data = json.loads(request.body)
        commande = get_object_or_404(Commande, id=data['commande_id'])
        nouvelle_table = get_object_or_404(Table, id=data['nouvelle_table_id'])

        # Vérifier que la table de destination est disponible ou c'est la même
        if nouvelle_table.statut == 'occupee' and commande.table != nouvelle_table:
            # Chercher si une commande active existe déjà sur cette table
            existe = Commande.objects.filter(
                table=nouvelle_table,
                statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
            ).exists()
            if existe:
                return JsonResponse({'success': False, 'message': f'La table {nouvelle_table.numero} a déjà une commande active'})

        with transaction.atomic():
            ancienne_table = commande.table
            commande.table = nouvelle_table
            commande.save(update_fields=['table'])
            # Libérer l'ancienne table si plus de commandes actives
            if ancienne_table:
                autres = Commande.objects.filter(
                    table=ancienne_table,
                    statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
                ).exclude(pk=commande.pk).exists()
                if not autres:
                    ancienne_table.statut = 'disponible'
                    ancienne_table.save()
            # Marquer la nouvelle table comme occupée
            nouvelle_table.statut = 'occupee'
            nouvelle_table.save()

        return JsonResponse({
            'success': True,
            'nouvelle_table_id': nouvelle_table.id,
            'nouvelle_table_num': nouvelle_table.numero,
            'ancienne_table_id': ancienne_table.id if ancienne_table else None,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
def resume_ventes_jour(request):
    """Résumé des ventes (jour ou période) pour le TPE restaurant."""
    from datetime import date as dt_date
    aujourd_hui = timezone.now().date()

    def parse_date(param, fallback):
        try:
            from datetime import datetime
            return datetime.strptime(request.GET[param], '%Y-%m-%d').date()
        except Exception:
            return fallback

    date_debut = parse_date('date_debut', aujourd_hui)
    date_fin   = parse_date('date_fin',   aujourd_hui)
    if date_fin < date_debut:
        date_fin = date_debut

    commandes = Commande.objects.filter(
        statut='payee',
        date_creation__date__gte=date_debut,
        date_creation__date__lte=date_fin,
    ).select_related('caissier', 'serveur', 'table')

    total_brut = sum(float(c.total) for c in commandes)
    total_net  = sum(c.total_net for c in commandes)
    nb_cmd     = commandes.count()

    # Tickets facturation : mode de paiement + liste détaillée
    par_mode = {}
    liste_tickets = []
    try:
        from facturation.models import Ticket as TicketCaisse
        tickets_jour = TicketCaisse.objects.filter(
            module='restaurant',
            date_creation__date__gte=date_debut,
            date_creation__date__lte=date_fin,
        ).select_related('cree_par').order_by('-date_creation')
        mode_noms = {
            'especes': 'Espèces', 'carte': 'Carte/TPE', 'carte_bancaire': 'Carte/TPE',
            'mobile': 'Mobile Money', 'mobile_money': 'Mobile Money',
            'orange_money': 'Orange Money', 'wave': 'Wave',
            'moov_money': 'Moov Money', 'mtn_money': 'MTN Money',
            'cheque': 'Chèque', 'virement': 'Virement', 'chambre': 'Chambre',
        }
        # Map commande_id → total_net pour éviter de sommer montant_paye
        # (montant_paye = ce que le client donne, peut dépasser le total en espèces)
        commande_net_map = {c.id: c.total_net for c in commandes}
        commande_table_map = {c.id: (c.table.numero if c.table else ('À emporter' if c.emporter else '')) for c in commandes}

        for tk in tickets_jour:
            m_raw = tk.mode_paiement or 'especes'
            m = mode_noms.get(m_raw, m_raw.replace('_', ' ').capitalize())
            montant_reel = commande_net_map.get(tk.objet_id, float(tk.montant_paye or 0))
            par_mode[m] = par_mode.get(m, 0) + float(montant_reel)
            caissier_nom = tk.cree_par.get_full_name() or tk.cree_par.username if tk.cree_par else ''
            table_ref = commande_table_map.get(tk.objet_id, '')
            liste_tickets.append({
                'numero':   tk.numero,
                'heure':    tk.date_creation.strftime('%H:%M'),
                'montant':  float(montant_reel),
                'mode':     m,
                'caissier': caissier_nom,
                'table':    table_ref,
            })
    except Exception:
        pass

    # Par caissier
    par_caissier = {}
    for c in commandes:
        nom = c.caissier.get_full_name() or c.caissier.username if c.caissier else 'Inconnu'
        par_caissier[nom] = par_caissier.get(nom, {'nb': 0, 'total': 0})
        par_caissier[nom]['nb'] += 1
        par_caissier[nom]['total'] += c.total_net

    periode = (date_debut.strftime('%d/%m/%Y') if date_debut == date_fin
               else f"{date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")
    return JsonResponse({
        'success': True,
        'date': periode,
        'nb_commandes': nb_cmd,
        'total_brut': total_brut,
        'total_net': total_net,
        'par_mode': par_mode,
        'par_caissier': [{'nom': k, **v} for k, v in par_caissier.items()],
        'tickets': liste_tickets,
    })


@require_module_access('restaurant')
def restaurant_tpe(request):
    """Interface TPE Restaurant"""
    from dashboard.models import Configuration
    from bar.models import CategorieBar

    # ── Catégories CUISINE niveau 1 (parent=null, hors boissons) ──
    mots_boisson = ['boisson', 'bière', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
    cats_niveau1 = [
        c for c in CategorieMenu.objects.filter(parent__isnull=True).order_by('ordre', 'nom')
        if not any(m in c.nom.lower() for m in mots_boisson)
    ]
    # Sous-catégories de "Plats Principaux"
    cat_plats_p = next((c for c in cats_niveau1 if 'plats principaux' in c.nom.lower()), None)
    sous_cats_plats = (
        list(CategorieMenu.objects.filter(parent=cat_plats_p).order_by('ordre', 'nom'))
        if cat_plats_p else []
    )
    # Toutes les catégories utiles pour filtrer les plats (niveau1 + sous-cats)
    ids_cat_cuisine = [c.id for c in cats_niveau1] + [c.id for c in sous_cats_plats]
    categories_cuisine = cats_niveau1  # compat template boissons

    # ── Catégories BAR (Cave) ──
    categories_bar = CategorieBar.objects.all().order_by('nom')

    # ── Plats CUISINE : avec fiche technique OU plats simples ──
    from cuisine.models import Plat as PlatCuisine
    from django.db.models import Q
    _plats_avec_ft = PlatCuisine.objects.filter(
        fiche_technique__isnull=False
    ).values_list('pk', flat=True)
    _q_plats = Q(cuisine_plat_id__in=_plats_avec_ft) | Q(is_simple=True)
    plats = PlatMenu.objects.filter(
        disponible=True, categorie__id__in=ids_cat_cuisine
    ).filter(_q_plats).select_related('categorie', 'categorie__parent') if ids_cat_cuisine else PlatMenu.objects.filter(
        disponible=True
    ).filter(_q_plats).select_related('categorie', 'categorie__parent')

    # ── Boissons de la Cave ──
    boissons_bar = BoissonBar.objects.filter(
        disponible=True, statut='actif'
    ).select_related(
        'categorie', 'shot_parent', 'shot_parent__parametrage_shot'
    ).order_by('categorie__nom', 'nom')

    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
    ).order_by('-date_modification').prefetch_related('lignes', 'table')
    config = Configuration.load()

    # ── Vérification stock plats ──
    for plat in plats:
        if plat.is_simple:
            plat.en_stock = True
            plat.stock_quantity = 999
            continue
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available
        ft = plat.fiche_technique
        if ft is not None and ft.lignes.exists():
            plat.stock_quantity = ft.max_portions_possibles()
        else:
            try:
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                plat.stock_quantity = int(ing.quantite_stock) if ing else 999
            except Exception:
                plat.stock_quantity = 999

    # ── top_cat_id pour chaque plat (pour le filtre niveau 1) ──
    for plat in plats:
        if plat.categorie and plat.categorie.parent_id:
            plat.top_cat_id = plat.categorie.parent_id
        else:
            plat.top_cat_id = plat.categorie_id if plat.categorie_id else 0

    # ── Accompagnements avec vérification stock ──
    accompagnements = []
    for acc in PlatMenu.objects.filter(disponible=True, is_accompagnement=True).select_related('categorie'):
        if acc.is_simple:
            acc.en_stock = True
            acc.stock_quantity = 999
        else:
            is_avail, _ = check_stock_availability(acc, 1)
            acc.en_stock = is_avail
            ft = acc.fiche_technique
            if ft is not None and ft.lignes.exists():
                acc.stock_quantity = ft.max_portions_possibles()
            else:
                try:
                    ing = Ingredient.objects.filter(nom__iexact=acc.nom).first()
                    acc.stock_quantity = int(ing.quantite_stock) if ing else 999
                except Exception:
                    acc.stock_quantity = 999
        accompagnements.append(acc)

    # ── Vérification stock boissons ──
    for b in boissons_bar:
        b.stock_quantity = b.stock_disponible

    from django.contrib.auth.models import Group, User as AuthUser
    try:
        groupe_serveurs = Group.objects.get(name='Serveuse/Serveur')
        serveurs = AuthUser.objects.filter(
            groups=groupe_serveurs, is_active=True
        ).order_by('first_name', 'last_name', 'username')
    except Group.DoesNotExist:
        serveurs = AuthUser.objects.none()

    # Chambres occupées pour report chambre
    from hotel.models import Reservation as HotelReservation
    chambres_occupees = HotelReservation.objects.filter(
        statut='en_cours'
    ).select_related('client', 'chambre').order_by('chambre__numero')

    # Opérateurs Mobile Money actifs
    from parametres.models import OperateurMobileMoney
    operateurs_mobile_money = OperateurMobileMoney.objects.filter(actif=True)

    # ── Menus VIP (tous modules, disponibles) ──
    from .models import Forfait
    forfaits_qs = Forfait.objects.filter(disponible=True).prefetch_related(
        'lignes__plat', 'lignes__boisson'
    )
    forfaits = []
    for forfait in forfaits_qs:
        # Vérifier la disponibilité de chaque composant
        en_stock = True
        for ligne in forfait.lignes.all():
            if ligne.plat:
                # Vérifier via cuisine_plat_id → FicheTechnique
                try:
                    plat_menu = PlatMenu.objects.filter(cuisine_plat_id=ligne.plat.pk).first()
                    if plat_menu:
                        ok, _ = check_stock_availability(plat_menu, ligne.quantite)
                        if not ok:
                            en_stock = False
                            break
                except Exception:
                    pass
            elif ligne.boisson:
                if ligne.boisson.stock_disponible < ligne.quantite:
                    en_stock = False
                    break
        forfait.en_stock = en_stock
        forfaits.append(forfait)

    context = {
        'categories': CategorieMenu.objects.all(),
        'plats': plats,
        'categories_cuisine': cats_niveau1,
        'sous_cats_plats': sous_cats_plats,
        'cat_plats_p_id': cat_plats_p.id if cat_plats_p else 0,
        'categories_bar': categories_bar,
        'boissons_bar': boissons_bar,
        'tables': tables,
        'accompagnements': accompagnements,
        'commandes_en_cours': commandes_en_cours_list.count(),
        'commandes_en_cours_list': commandes_en_cours_list,
        'config': config,
        'serveurs': serveurs,
        'chambres_occupees': chambres_occupees,
        'forfaits': forfaits,
        'operateurs_mobile_money': operateurs_mobile_money,
    }
    return render(request, 'restaurant/index.html', context)


@require_module_access('restaurant')
@require_POST
def ajouter_boisson_commande(request):
    """Ajoute une boisson de la Cave à une commande restaurant — décrémente stock BoissonBar"""
    try:
        from bar.models import BoissonBar, MouvementStockBar
        data        = json.loads(request.body)
        table_id    = data.get('table_id')
        commande_id = data.get('commande_id')
        boisson_id  = data.get('boisson_id')
        client_nom  = data.get('client', '')

        boisson = get_object_or_404(BoissonBar, id=boisson_id)

        if boisson.est_en_rupture:
            return JsonResponse({'success': False, 'message': f'{boisson.nom} est en rupture de stock'})

        serveur_user = _resoudre_serveur(data.get('serveur', '')) or request.user
        # Récupérer ou créer la commande
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
            if commande.serveur == request.user and serveur_user != request.user:
                commande.serveur = serveur_user
                commande.save(update_fields=['serveur'])
        elif table_id:
            table = get_object_or_404(Table, id=table_id)
            commande = Commande.objects.filter(
                table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
            ).first()
            if not commande:
                commande = Commande.objects.create(
                    table=table, serveur=serveur_user,
                    statut='en_attente', nom_client=client_nom
                )
                table.statut = 'occupee'
                table.save()
        elif data.get('emporter'):
            commande = Commande.objects.create(
                table=None, serveur=serveur_user,
                statut='en_attente', nom_client=client_nom or 'À emporter',
            )
        else:
            return JsonResponse({'success': False, 'message': 'Table ou mode emporter requis'})

        with transaction.atomic():
            # Chercher ligne existante pour cette boisson
            ligne = LigneCommande.objects.filter(
                commande=commande, boisson=boisson, plat=None
            ).first()

            if ligne:
                ligne.quantite += 1
                ligne.save()
            else:
                ligne = LigneCommande.objects.create(
                    commande=commande,
                    plat=None,
                    boisson=boisson,
                    accompagnement=None,
                    quantite=1,
                    prix_unitaire=boisson.prix,
                    nom_article=boisson.nom,
                )

            # Décrémenter stock Cave
            boisson.destock(1, f'Vente Restaurant #{commande.id}', request.user)

            commande.total = float(commande.total) + float(boisson.prix)
            commande.save()

        data_out = _serialize_commande(commande)
        return JsonResponse({'success': True, 'commande_id': commande.id, **data_out})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
@require_POST
def ajouter_forfait_commande(request):
    """
    Ajoute un Forfait (Menu VIP) à une commande restaurant.
    Vérifie et décrémente le stock de chaque composant (plats cuisine + boissons cave).
    """
    try:
        from .models import Forfait
        data = json.loads(request.body)
        forfait_id  = data.get('forfait_id')
        table_id    = data.get('table_id')
        commande_id = data.get('commande_id')
        client_nom  = data.get('client', '')

        forfait = get_object_or_404(Forfait, id=forfait_id, module='restaurant', disponible=True)
        lignes_forfait = forfait.lignes.select_related('plat', 'boisson').all()

        # ── 1. Vérification stock de tous les composants ──
        erreurs = []
        for lf in lignes_forfait:
            if lf.plat:
                plat_menu = PlatMenu.objects.filter(cuisine_plat_id=lf.plat.pk).first()
                if plat_menu:
                    ok, msg = check_stock_availability(plat_menu, lf.quantite)
                    if not ok:
                        erreurs.append(f"{lf.plat.nom}: {msg}")
            elif lf.boisson:
                if lf.boisson.stock_disponible < lf.quantite:
                    erreurs.append(
                        f"{lf.boisson.nom}: stock insuffisant "
                        f"({lf.boisson.stock_disponible} dispo, {lf.quantite} requis)"
                    )
        if erreurs:
            return JsonResponse({'success': False, 'message': "Stock insuffisant :\n" + "\n".join(erreurs)})

        # ── 2. Récupérer ou créer la commande ──
        serveur_user = _resoudre_serveur(data.get('serveur', '')) or request.user
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
            if commande.serveur == request.user and serveur_user != request.user:
                commande.serveur = serveur_user
                commande.save(update_fields=['serveur'])
        elif table_id:
            table = get_object_or_404(Table, id=table_id)
            commande = Commande.objects.filter(
                table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
            ).first()
            if not commande:
                commande = Commande.objects.create(
                    table=table, serveur=serveur_user,
                    statut='en_attente', nom_client=client_nom
                )
                table.statut = 'occupee'
                table.save()
        elif data.get('emporter'):
            commande = Commande.objects.create(
                table=None, serveur=serveur_user,
                statut='en_attente', nom_client=client_nom or 'À emporter',
            )
        else:
            return JsonResponse({'success': False, 'message': 'Table ou mode emporter requis'})

        with transaction.atomic():
            # ── 3. Créer une LigneCommande unique pour le forfait ──
            LigneCommande.objects.create(
                commande=commande,
                plat=None,
                boisson=None,
                accompagnement=None,
                quantite=1,
                prix_unitaire=forfait.prix,
                nom_article=forfait.nom,
            )
            commande.total = float(commande.total) + float(forfait.prix)
            commande.save()

            # ── 4. Déduire stock de chaque composant ──
            for lf in lignes_forfait:
                if lf.plat:
                    plat_menu = PlatMenu.objects.filter(cuisine_plat_id=lf.plat.pk).first()
                    if plat_menu:
                        process_stock_movement(
                            plat_menu, lf.quantite, 'sortie', request.user,
                            f"Forfait {forfait.nom} — Commande #{commande.id}"
                        )
                elif lf.boisson:
                    lf.boisson.destock(
                        lf.quantite,
                        f'Forfait {forfait.nom} — Commande #{commande.id}',
                        request.user,
                    )

        data_out = _serialize_commande(commande)
        return JsonResponse({'success': True, 'commande_id': commande.id, **data_out})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE RÉSERVATIONS RESTAURANT
# ═══════════════════════════════════════════════════════════════════════════════

from django.views.decorators.http import require_POST as _require_POST
from django.http import JsonResponse as _JsonResponse
import json as _json

@login_required
def reservation_list(request):
    """Page principale de gestion des réservations restaurant."""
    from django.utils import timezone
    from datetime import timedelta

    today     = timezone.now().date()
    date_str  = request.GET.get('date', str(today))
    try:
        from datetime import date as _date
        date_filtre = _date.fromisoformat(date_str)
    except Exception:
        date_filtre = today

    # Réservations du jour sélectionné
    resa_jour = Reservation.objects.filter(
        date_reservation__date=date_filtre
    ).select_related('table').order_by('date_reservation')

    # Réservations futures (hors aujourd'hui)
    resa_futures = Reservation.objects.filter(
        date_reservation__date__gt=today,
        statut='confirmee'
    ).select_related('table').order_by('date_reservation')[:20]

    # Stats du jour
    stats = {
        'total':     resa_jour.count(),
        'confirmees':resa_jour.filter(statut='confirmee').count(),
        'terminees': resa_jour.filter(statut='terminee').count(),
        'annulees':  resa_jour.filter(statut='annulee').count(),
        'personnes': sum(r.nombre_personnes for r in resa_jour),
    }

    tables = Table.objects.all().order_by('numero')

    context = {
        'resa_jour':    resa_jour,
        'resa_futures': resa_futures,
        'tables':       tables,
        'stats':        stats,
        'date_filtre':  date_filtre,
        'today':        today,
    }
    return render(request, 'restaurant/reservation_list.html', context)


@login_required
def reservation_create(request):
    """Créer une réservation depuis le formulaire."""
    if request.method == 'POST':
        from django.utils import timezone
        from django.contrib import messages as _msg
        try:
            table_id       = request.POST.get('table')
            client_nom     = request.POST.get('client_nom', '').strip()
            client_tel     = request.POST.get('client_telephone', '').strip()
            date_str       = request.POST.get('date_reservation')
            nb_personnes   = int(request.POST.get('nombre_personnes', 1))
            note           = request.POST.get('note', '').strip()

            if not all([table_id, client_nom, date_str]):
                _msg.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return redirect('restaurant:reservation_list')

            from django.utils.dateparse import parse_datetime
            date_res = parse_datetime(date_str)
            if not date_res:
                _msg.error(request, 'Format de date invalide.')
                return redirect('restaurant:reservation_list')

            table = get_object_or_404(Table, pk=table_id)

            # Vérifier conflit sur la même table même créneau (±1h)
            from datetime import timedelta
            conflit = Reservation.objects.filter(
                table=table,
                statut='confirmee',
                date_reservation__range=(
                    date_res - timedelta(hours=1),
                    date_res + timedelta(hours=1)
                )
            ).exists()
            if conflit:
                _msg.warning(request, f'⚠️ La table {table.numero} est déjà réservée sur ce créneau (±1h).')
                return redirect('restaurant:reservation_list')

            Reservation.objects.create(
                table=table,
                client_nom=client_nom,
                client_telephone=client_tel,
                date_reservation=date_res,
                nombre_personnes=nb_personnes,
                note=note,
                statut='confirmee',
            )
            # Marquer la table comme réservée si la résa est aujourd'hui
            if date_res.date() == timezone.now().date():
                table.statut = 'reservee'
                table.save()

            _msg.success(request, f'✅ Réservation créée pour {client_nom} — {table.numero}')
        except Exception as e:
            _msg.error(request, f'Erreur : {e}')
        return redirect('restaurant:reservation_list')
    return redirect('restaurant:reservation_list')


@login_required
def reservation_update(request, pk):
    """Modifier une réservation existante."""
    from django.contrib import messages as _msg
    resa = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        try:
            from django.utils.dateparse import parse_datetime
            resa.client_nom       = request.POST.get('client_nom', resa.client_nom).strip()
            resa.client_telephone = request.POST.get('client_telephone', '').strip()
            date_str = request.POST.get('date_reservation')
            if date_str:
                date_res = parse_datetime(date_str)
                if date_res:
                    resa.date_reservation = date_res
            resa.nombre_personnes = int(request.POST.get('nombre_personnes', resa.nombre_personnes))
            resa.note             = request.POST.get('note', '').strip()
            resa.statut           = request.POST.get('statut', resa.statut)
            resa.save()
            # Libérer table si annulée
            if resa.statut == 'annulee' and resa.table.statut == 'reservee':
                resa.table.statut = 'libre'
                resa.table.save()
            _msg.success(request, f'Réservation de {resa.client_nom} mise à jour.')
        except Exception as e:
            _msg.error(request, f'Erreur : {e}')
        return redirect('restaurant:reservation_list')
    tables = Table.objects.all().order_by('numero')
    return render(request, 'restaurant/reservation_form.html', {
        'resa': resa, 'tables': tables, 'mode': 'edit'
    })


@login_required
def reservation_cancel(request, pk):
    """Annuler une réservation."""
    from django.contrib import messages as _msg
    resa = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        resa.statut = 'annulee'
        resa.save()
        if resa.table.statut == 'reservee':
            resa.table.statut = 'libre'
            resa.table.save()
        _msg.success(request, f'Réservation de {resa.client_nom} annulée.')
    return redirect('restaurant:reservation_list')


@require_module_access('restaurant')
@_require_POST
def reservation_api_statut(request):
    """API JSON — changer le statut d'une réservation."""
    try:
        data   = _json.loads(request.body)
        pk     = data.get('reservation_id')
        statut = data.get('statut')
        resa   = get_object_or_404(Reservation, pk=pk)
        resa.statut = statut
        resa.save()
        if statut == 'annulee' and resa.table.statut == 'reservee':
            resa.table.statut = 'libre'
            resa.table.save()
        elif statut == 'terminee':
            resa.table.statut = 'occupee'
            resa.table.save()
        return _JsonResponse({'success': True})
    except Exception as e:
        return _JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_module_access('restaurant')
def imprimer_addition(request, commande_id):
    """Pré-facture (addition) : affiche les articles sans encaisser ni clôturer le ticket."""
    commande = get_object_or_404(Commande, id=commande_id)
    lignes = commande.lignes.select_related('plat', 'accompagnement', 'boisson').all()
    from dashboard.models import Configuration
    config = Configuration.load()
    montant_remise = float(commande.total) * float(commande.remise_pct) / 100 if commande.remise_pct else 0
    return render(request, 'restaurant/addition_print.html', {
        'commande': commande,
        'lignes': lignes,
        'config': config,
        'montant_remise': montant_remise,
    })
