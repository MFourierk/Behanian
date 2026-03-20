from utils.permissions import require_module_access
from django.shortcuts import render, redirect, get_object_or_404
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
from bar.models import BoissonBar, MouvementStockBar
from facturation.models import Ticket, generate_ticket_numero
from hotel.models import Client as HotelClient

from cuisine.utils import check_stock_availability, process_stock_movement
from cuisine.models import Ingredient
from .views_extension import create_reservation, update_reservation_status

@require_module_access('restaurant')
def restaurant_index(request):
    """Vue principale du restaurant"""
    
    # Synchronisation des Boissons du Bar vers le Menu Restaurant
    # Cela permet de lister les boissons de la Cave dans la grille et d'utiliser la déduction de stock existante
    try:
        cat_boissons, _ = CategorieMenu.objects.get_or_create(nom="Boissons", defaults={'ordre': 100})
        boissons_bar = BoissonBar.objects.filter(disponible=True)
        
        for b in boissons_bar:
            # On utilise get_or_create avec le nom exact
            # Note: Le système de stock utilise déjà le nom pour faire le lien (voir plus bas)
            plat, created = PlatMenu.objects.get_or_create(
                nom__iexact=b.nom,
                defaults={
                    'nom': b.nom,
                    'categorie': cat_boissons,
                    'prix': b.prix,
                    'description': b.description or "",
                    'temps_preparation': 0,
                    'disponible': b.disponible,
                    'image': b.image  # Copie de l'image
                }
            )
            if not created:
                # Si le plat existait déjà, on met à jour les infos
                plat.prix = b.prix
                plat.disponible = b.disponible
                plat.image = b.image
                plat.save()
    except Exception as e:
        print(f"Erreur synchro boissons: {e}")

    # Récupérer toutes les catégories et plats
    categories = CategorieMenu.objects.all()
    plats = PlatMenu.objects.filter(disponible=True)
    
    # Commandes en cours (Non payées)
    commandes_en_cours_list = Commande.objects.filter(statut__in=['en_attente', 'en_preparation', 'prete', 'servie']).order_by('-date_modification')
    commandes_en_cours = commandes_en_cours_list.count()
    
    # Tables
    tables = Table.objects.all()

    # Réservations actives
    reservations = Reservation.objects.filter(
        statut='confirmee',
        date_reservation__gte=timezone.now()
    ).order_by('date_reservation')
    
    # Vérification du stock pour chaque plat
    # On ajoute un attribut temporaire 'en_stock' aux objets plats pour l'affichage
    for plat in plats:
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available
        
        # Calcul de la quantité exacte disponible (Venant de la Cuisine ou du Bar)
        if hasattr(plat, 'fiche_technique'):
            plat.stock_quantity = plat.fiche_technique.max_portions_possibles()
        elif plat.categorie and any(x in plat.categorie.nom.lower() for x in ['boisson', 'bière', 'vin', 'alcool', 'jus', 'soda']):
            try:
                # Importation locale pour éviter circularité si nécessaire
                # Mais BoissonBar est déjà importé en haut
                boisson = BoissonBar.objects.get(nom__iexact=plat.nom)
                plat.stock_quantity = int(boisson.quantite_stock)
            except:
                plat.stock_quantity = 999
        else:
            # Fallback: Recherche d'un ingrédient homonyme (ex: Alloco) si pas de fiche technique
            try:
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                if ing:
                    plat.stock_quantity = int(ing.quantite_stock)
                else:
                    plat.stock_quantity = 999
            except:
                 plat.stock_quantity = 999
        
    # Accompagnements (Définis dans le module Cuisine via le flag is_accompagnement)
    accompagnements = plats.filter(is_accompagnement=True)
        
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

@require_module_access('restaurant')
@require_POST
def valider_commande(request):
    """Valide une commande (Paiement uniquement maintenant, l'ajout se fait en temps réel)"""
    try:
        data = json.loads(request.body)
        commande_id = data.get('commande_id')
        action = data.get('action', 'paiement')
        montant_encaisse = Decimal(str(data.get('montant_encaisse', 0)))
        client_name = data.get('client', '')

        if not commande_id:
            return JsonResponse({'success': False, 'message': 'ID Commande manquant'})
            
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Mise à jour infos client si fourni
        if client_name:
            commande.nom_client = client_name
            commande.save()

        if action == 'paiement':
            if commande.total <= 0:
                 return JsonResponse({'success': False, 'message': 'Le total est nul.'})

            serveur_nom = data.get('serveur', '')
            if not serveur_nom:
                return JsonResponse({'success': False, 'message': 'Veuillez sélectionner un serveur avant de valider.'})

            with transaction.atomic():
                commande.statut = 'payee'
                commande.save()
                
                if commande.table:
                    commande.table.statut = 'disponible'
                    commande.table.save()
                
                # Génération Ticket
                numero_ticket = generate_ticket_numero()
                
                all_items_objs = LigneCommande.objects.filter(commande=commande)
                
                # Génération du contenu HTML pour le Ticket
                services_html = ""

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

                # Création du Ticket
                ticket = Ticket.objects.create(
                    numero=numero_ticket,
                    module='restaurant',
                    montant_total=commande.total,
                    client=None,
                    contenu=services_html,
                    objet_id=commande.id,
                    montant_paye=montant_encaisse,
                    mode_paiement=data.get('mode_paiement', 'especes'),
                    cree_par=request.user,
                    imprime=True
                )

                # Si mode chambre : lier les articles à la réservation hôtel
                reservation_hotel_id = data.get('reservation_hotel_id')
                mode_paiement_val = data.get('mode_paiement', 'especes')
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
                    except Exception:
                        pass

                # Rendu ticket thermique avec serveur
                ticket_html = render_to_string('facturation/ticket_print_thermal.html', {
                    'ticket':  ticket,
                    'serveur': serveur_nom,
                    'is_original': True
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
            for ligne in commande.lignes.all():
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
            
            # 2. Mettre à jour le statut
            commande.statut = 'annulee'
            commande.save()
            
            # 3. Libérer la table
            if commande.table:
                commande.table.statut = 'disponible'
                commande.table.save()
                
        return JsonResponse({'success': True, 'message': 'Commande annulée avec succès'})
        
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
                'plat_id': l.plat.id
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

        return JsonResponse({
            'success': True,
            'commande': {
                'id':       commande.id,
                'table_id': commande.table.id if commande.table else None,
                'client':   commande.nom_client,
                'items':    items,
                'total':    float(commande.total)
            }
        })
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
        
        items = []
        for l in commande.lignes.all().select_related('plat', 'accompagnement').order_by('id'):
            nom_affiche = (l.get_nom if hasattr(l,"get_nom") else l.nom_article or (l.plat.nom if l.plat else (l.boisson.nom if hasattr(l,"boisson") and l.boisson else "?")))
            if l.accompagnement:
                nom_affiche += f" (+ {l.accompagnement.nom})"
            items.append({
                'id': l.id,
                'nom': nom_affiche,
                'prix': float(l.prix_unitaire),
                'quantite': l.quantite,
                'plat_id': l.plat.id,
                'has_acc': bool(l.accompagnement)
            })

        return JsonResponse({
            'success': True, 
            'items': items,
            'total': float(commande.total)
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
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
        elif table_id:
            table = get_object_or_404(Table, id=table_id)
            # Chercher commande active
            commande = Commande.objects.filter(table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']).first()
            if not commande:
                # Créer nouvelle commande
                commande = Commande.objects.create(
                    table=table, 
                    serveur=request.user, 
                    statut='en_preparation',
                    nom_client=data.get('client', '')
                )
                table.statut = 'occupee'
                table.save()
        else:
            return JsonResponse({'success': False, 'message': 'Table requise'})

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
            
        # 5. Retourner l'état complet de la commande pour rafraichissement
        items = []
        for l in commande.lignes.all().select_related('plat', 'accompagnement', 'boisson').order_by('id'):
            nom_affiche = l.get_nom if hasattr(l, 'get_nom') else (l.nom_article or (l.plat.nom if l.plat else '?'))
            if l.plat and l.accompagnement:
                nom_affiche += f" (+ {l.accompagnement.nom})"
            items.append({
                'id': l.id,
                'nom': nom_affiche,
                'prix': float(l.prix_unitaire),
                'quantite': l.quantite,
            })
            
        return JsonResponse({
            'success': True,
            'commande_id': commande.id,
            'items': items,
            'total': float(commande.total),
            'client': commande.nom_client
        })

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
            
            if delta > 0:
                # Ajout (+1)
                # Check stock Plat
                is_available, error_msg = check_stock_availability(plat, 1)
                if not is_available: return JsonResponse({'success': False, 'message': error_msg})
                
                # Check stock Accompagnement
                if ligne.accompagnement:
                     is_acc, acc_err = check_stock_availability(ligne.accompagnement, 1)
                     if not is_acc: return JsonResponse({'success': False, 'message': f"Accompagnement indisponible: {ligne.accompagnement.nom}"})

                # Update
                ligne.quantite += 1
                ligne.save()
                
                # Destock
                process_stock_movement(plat, 1, 'sortie', request.user, f"Ajout Restaurant #{commande.id}")
                if ligne.accompagnement:
                    process_stock_movement(ligne.accompagnement, 1, 'sortie', request.user, f"Ajout Accompagnement #{commande.id}")
                
                commande.total = float(commande.total) + float(prix_unit)
                
            else:
                # Retrait (-1)
                if ligne.quantite > 1:
                    ligne.quantite -= 1
                    ligne.save()
                    
                    # Restock
                    process_stock_movement(plat, 1, 'entree', request.user, f"Retrait Restaurant #{commande.id}")
                    if ligne.accompagnement:
                        process_stock_movement(ligne.accompagnement, 1, 'entree', request.user, f"Retrait Accompagnement #{commande.id}")
                         
                    commande.total = float(commande.total) - float(prix_unit)
                    
                else:
                    # Suppression complète
                    process_stock_movement(plat, 1, 'entree', request.user, f"Retrait Restaurant #{commande.id}")
                    if ligne.accompagnement:
                        process_stock_movement(ligne.accompagnement, 1, 'entree', request.user, f"Retrait Accompagnement #{commande.id}")
                    
                    ligne.delete()
                    commande.total = float(commande.total) - float(prix_unit)

            if commande.total < 0: commande.total = 0
            commande.save()

        # Retour état
        items = []
        try:
             # On re-check si la commande existe encore (normalement oui)
             cmd = Commande.objects.get(id=commande.id)
             for l in cmd.lignes.all().select_related('plat', 'accompagnement').order_by('id'):
                nom_affiche = (l.get_nom if hasattr(l,"get_nom") else l.nom_article or (l.plat.nom if l.plat else (l.boisson.nom if hasattr(l,"boisson") and l.boisson else "?")))
                if l.accompagnement:
                    nom_affiche += f" (+ {l.accompagnement.nom})"
                items.append({
                    'id': l.id,
                    'nom': nom_affiche,
                    'prix': float(l.prix_unitaire),
                    'quantite': l.quantite,
                    'plat_id': l.plat.id,
                    'has_acc': bool(l.accompagnement)
                })
        except Exception:
             pass
            
        return JsonResponse({
            'success': True,
            'items': items,
            'total': float(commande.total)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_module_access('restaurant')
def restaurant_tpe(request):
    """Interface TPE Restaurant"""
    from dashboard.models import Configuration
    from bar.models import CategorieBar

    # ── Catégories CUISINE (exclure celles qui contiennent 'boisson') ──
    mots_boisson = ['boisson', 'bière', 'biere', 'vin', 'alcool', 'soda', 'jus', 'soft', 'liqueur', 'spiritueux']
    categories_cuisine = [
        c for c in CategorieMenu.objects.all()
        if not any(m in c.nom.lower() for m in mots_boisson)
    ]

    # ── Catégories BAR (Cave) ──
    categories_bar = CategorieBar.objects.all().order_by('nom')

    # ── Plats CUISINE uniquement (hors boissons) ──
    ids_cat_cuisine = [c.id for c in categories_cuisine]
    plats = PlatMenu.objects.filter(
        disponible=True,
        categorie__id__in=ids_cat_cuisine
    ) if ids_cat_cuisine else PlatMenu.objects.filter(disponible=True)

    # ── Boissons de la Cave ──
    boissons_bar = BoissonBar.objects.filter(
        disponible=True, statut='actif'
    ).select_related('categorie').order_by('categorie__nom', 'nom')

    tables = Table.objects.all()
    commandes_en_cours_list = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
    ).order_by('-date_modification').prefetch_related('lignes', 'table')
    accompagnements = PlatMenu.objects.filter(disponible=True, is_accompagnement=True)
    config = Configuration.load()

    # ── Vérification stock plats ──
    for plat in plats:
        is_available, _ = check_stock_availability(plat, 1)
        plat.en_stock = is_available
        if hasattr(plat, 'fiche_technique'):
            plat.stock_quantity = plat.fiche_technique.max_portions_possibles()
        else:
            try:
                ing = Ingredient.objects.filter(nom__iexact=plat.nom).first()
                plat.stock_quantity = int(ing.quantite_stock) if ing else 999
            except:
                plat.stock_quantity = 999

    # ── Vérification stock boissons ──
    for b in boissons_bar:
        b.stock_quantity = int(b.quantite_stock)

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

    context = {
        'categories': CategorieMenu.objects.all(),
        'plats': plats,
        'categories_cuisine': categories_cuisine,
        'categories_bar': categories_bar,
        'boissons_bar': boissons_bar,
        'tables': tables,
        'accompagnements': accompagnements,
        'commandes_en_cours': commandes_en_cours_list.count(),
        'commandes_en_cours_list': commandes_en_cours_list,
        'config': config,
        'serveurs': serveurs,
        'chambres_occupees': chambres_occupees,
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

        # Récupérer ou créer la commande
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
        elif table_id:
            table = get_object_or_404(Table, id=table_id)
            commande = Commande.objects.filter(
                table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
            ).first()
            if not commande:
                commande = Commande.objects.create(
                    table=table, serveur=request.user,
                    statut='en_preparation', nom_client=client_nom
                )
                table.statut = 'occupee'
                table.save()
        else:
            return JsonResponse({'success': False, 'message': 'Table requise'})

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
            boisson.quantite_stock = max(0, boisson.quantite_stock - 1)
            boisson.save()
            MouvementStockBar.objects.create(
                boisson=boisson,
                type_mouvement='sortie',
                quantite=1,
                commentaire=f'Vente Restaurant #{commande.id}',
                utilisateur=request.user
            )

            commande.total = float(commande.total) + float(boisson.prix)
            commande.save()

        # Retourner état complet
        items = []
        for l in commande.lignes.all().order_by('id'):
            nom = l.get_nom
            items.append({
                'id':       l.id,
                'nom':      nom,
                'prix':     float(l.prix_unitaire),
                'quantite': l.quantite,
            })

        return JsonResponse({
            'success':    True,
            'commande_id': commande.id,
            'items':      items,
            'total':      float(commande.total),
            'client':     commande.nom_client
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})
