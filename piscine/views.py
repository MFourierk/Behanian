from utils.permissions import require_module_access
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, F
from django.db import models as db_models
from .models import AccesPiscine, TarifPiscine, ConsommationPiscine
from decimal import Decimal
import json


@require_module_access('piscine')
def piscine_index(request):
    today = timezone.now().date()

    # Stats
    acces_actifs   = AccesPiscine.objects.filter(date_sortie__isnull=True)
    entrees_jour   = AccesPiscine.objects.filter(date_entree__date=today).count()
    visiteurs      = acces_actifs.filter(type_client='visiteur').count()
    heberges       = acces_actifs.filter(type_client='heberge').count()
    # Recette = entrées payantes + toutes les consommations du jour
    acces_jour = AccesPiscine.objects.filter(date_entree__date=today)
    recette_entrees = acces_jour.aggregate(s=Sum('prix_total'))['s'] or 0
    recette_consos  = ConsommationPiscine.objects.filter(
        acces__date_entree__date=today
    ).aggregate(s=Sum(F('quantite') * F('prix_unitaire')))['s'] or 0
    recette_jour = recette_entrees + recette_consos

    # Tarifs
    tarif_v_adulte = TarifPiscine.objects.filter(type_tarif='adulte_visiteur').first()
    tarif_v_enfant = TarifPiscine.objects.filter(type_tarif='enfant_visiteur').first()

    # Résidents hôtel actuellement en séjour
    from hotel.models import Reservation as HotelReservation
    residents = HotelReservation.objects.filter(
        statut='en_cours'
    ).select_related('client', 'chambre').order_by('chambre__numero')

    # Boissons et plats pour commandes
    from bar.models import BoissonBar, CategorieBar
    from restaurant.models import PlatMenu, CategorieMenu
    boissons    = BoissonBar.objects.filter(statut='actif', disponible=True).select_related('categorie').order_by('categorie__nom', 'nom')
    cats_bar    = CategorieBar.objects.order_by('nom')
    plats       = PlatMenu.objects.filter(disponible=True).select_related('categorie').order_by('categorie__nom', 'nom')
    cats_resto  = CategorieMenu.objects.exclude(nom__icontains='boisson').order_by('nom')

    # Accès du jour avec consommations
    acces_liste = AccesPiscine.objects.filter(
        date_entree__date=today
    ).prefetch_related('consommations').order_by('-date_entree')

    context = {
        'entrees_jour': entrees_jour,
        'actuellement': acces_actifs.count(),
        'visiteurs': visiteurs,
        'heberges': heberges,
        'recette_jour': int(recette_jour),
        'tarif_v_adulte': tarif_v_adulte,
        'tarif_v_enfant': tarif_v_enfant,
        'residents': residents,
        'boissons': boissons,
        'cats_bar': cats_bar,
        'plats': plats,
        'cats_resto': cats_resto,
        'acces_liste': acces_liste,
        'acces_actifs': acces_actifs.select_related().prefetch_related('consommations'),
    }
    return render(request, 'piscine/index.html', context)


@require_module_access('piscine')
@require_POST
def enregistrer_entree(request):
    """Enregistrer une entrée piscine."""
    try:
        data = json.loads(request.body)
        type_client  = data.get('type_client', 'visiteur')
        nom_client   = data.get('nom_client', '').strip()
        nb_adultes   = int(data.get('nb_adultes', 0))
        nb_enfants   = int(data.get('nb_enfants', 0))
        if type_client != 'heberge' and nb_adultes < 1 and nb_enfants < 1:
            return JsonResponse({'success': False, 'error': 'Veuillez indiquer au moins 1 personne.'})

        if not nom_client:
            return JsonResponse({'success': False, 'error': 'Nom du client requis'})

        # Calcul prix
        if type_client == 'heberge':
            prix_total = Decimal('0')
        else:
            t_adulte = TarifPiscine.objects.filter(type_tarif='adulte_visiteur').first()
            t_enfant = TarifPiscine.objects.filter(type_tarif='enfant_visiteur').first()
            if not t_adulte:
                return JsonResponse({'success': False, 'error': 'Tarif adulte non configuré.'})
            prix_adulte = (t_adulte.prix_unitaire * nb_adultes) if nb_adultes else Decimal('0')
            prix_enfant = (t_enfant.prix_unitaire * nb_enfants) if t_enfant and nb_enfants else Decimal('0')
            prix_total  = prix_adulte + prix_enfant

        # Lier à la réservation hôtel si résident
        reservation_hotel = None
        reservation_id = data.get('reservation_id')
        if type_client == 'heberge' and reservation_id:
            from hotel.models import Reservation as HotelReservation
            try:
                reservation_hotel = HotelReservation.objects.get(id=reservation_id, statut='en_cours')
            except HotelReservation.DoesNotExist:
                pass

        create_kwargs = dict(
            nom_client=nom_client,
            type_client=type_client,
            prix_total=prix_total,
            enregistre_par=request.user,
        )
        # Champs ajoutés par migration — présents seulement si migrate a tourné
        from django.db import connection
        cols = [r[1] for r in connection.cursor().execute('PRAGMA table_info(piscine_accespiscine)').fetchall()]
        if 'nb_adultes' in cols:
            create_kwargs['nb_adultes'] = nb_adultes
            create_kwargs['nb_enfants'] = nb_enfants
        if 'reservation_hotel_id' in cols:
            create_kwargs['reservation_hotel'] = reservation_hotel
        acces = AccesPiscine.objects.create(**create_kwargs)

        return JsonResponse({
            'success': True,
            'acces_id': acces.id,
            'nom': acces.nom_client,
            'type': acces.get_type_client_display(),
            'prix': float(prix_total),
            'message': f"Entrée enregistrée — {nom_client} ({acces.get_type_client_display()})"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('piscine')
@require_POST
def ajouter_consommation(request, acces_id):
    """Ajouter une consommation (plat ou boisson) à un accès piscine."""
    try:
        acces = get_object_or_404(AccesPiscine, id=acces_id)
        data  = json.loads(request.body)

        type_article = data.get('type')  # 'boisson' ou 'plat'
        article_id   = data.get('id')
        quantite     = int(data.get('quantite', 1))

        if type_article == 'boisson':
            from bar.models import BoissonBar, MouvementStockBar
            boisson = get_object_or_404(BoissonBar, id=article_id)
            if boisson.est_en_rupture:
                return JsonResponse({'success': False, 'error': f'{boisson.nom} est en rupture de stock'})
            ConsommationPiscine.objects.create(
                acces=acces,
                produit=boisson.nom,
                quantite=quantite,
                prix_unitaire=boisson.prix,
            )
            boisson.quantite_stock = max(0, boisson.quantite_stock - quantite)
            boisson.save()
            MouvementStockBar.objects.create(
                boisson=boisson, type_mouvement='sortie',
                quantite=quantite, commentaire=f'Piscine #{acces.id}',
                utilisateur=request.user
            )
            # Lier à la réservation hôtel si résident
            reservation_hotel = getattr(acces, 'reservation_hotel', None)
            if reservation_hotel:
                from hotel.models import Consommation as HotelConso
                HotelConso.objects.create(
                    reservation=reservation_hotel,
                    type_service='piscine',
                    boisson=boisson,
                    nom=f'[Piscine#{acces.id}] {boisson.nom}',
                    quantite=quantite,
                    prix_unitaire=boisson.prix,
                )
            nom = boisson.nom
            prix = float(boisson.prix)

        elif type_article == 'plat':
            from restaurant.models import PlatMenu
            plat = get_object_or_404(PlatMenu, id=article_id)
            ConsommationPiscine.objects.create(
                acces=acces,
                produit=plat.nom,
                quantite=quantite,
                prix_unitaire=plat.prix,
            )
            # Lier à la réservation hôtel si résident
            reservation_hotel = getattr(acces, 'reservation_hotel', None)
            if reservation_hotel:
                from hotel.models import Consommation as HotelConso
                HotelConso.objects.create(
                    reservation=reservation_hotel,
                    type_service='piscine',
                    plat=plat,
                    nom=f'[Piscine#{acces.id}] {plat.nom}',
                    quantite=quantite,
                    prix_unitaire=plat.prix,
                )
            nom = plat.nom
            prix = float(plat.prix)
        else:
            return JsonResponse({'success': False, 'error': 'Type article invalide'})

        # Recalculer total consommations
        total_conso = sum(c.get_total() for c in acces.consommations.all())

        return JsonResponse({
            'success': True,
            'message': f'{nom} x{quantite} ajouté',
            'total_consommations': float(total_conso),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('piscine')
@require_POST
def encaisser_sortie(request, acces_id):
    """Encaisser et enregistrer la sortie d'un client."""
    try:
        from facturation.models import Ticket, generate_ticket_numero
        acces = get_object_or_404(AccesPiscine, id=acces_id)
        data  = json.loads(request.body)
        mode_paiement = data.get('mode_paiement', 'especes')
        montant_recu  = Decimal(str(data.get('montant_recu', 0)))
        sur_chambre   = data.get('sur_chambre', False)

        # Total = entrée + consommations
        total_conso = sum(c.get_total() for c in acces.consommations.all())
        total       = acces.prix_total + total_conso

        # Validation montant seulement si paiement direct visiteur
        if not sur_chambre and montant_recu < total and acces.type_client == 'visiteur':
            return JsonResponse({'success': False, 'error': f'Montant insuffisant. Total : {int(total)} F'})

        # Marquer sortie
        acces.date_sortie = timezone.now()
        acces.save()

        nb_total = acces.nb_adultes + acces.nb_enfants

        # Mode CHAMBRE : ajouter les consos à la réservation hôtel sans créer ticket séparé
        if sur_chambre and acces.reservation_hotel:
            reservation = acces.reservation_hotel
            from hotel.models import Consommation as HotelConso
            # Ajouter entrée si payante (hébergé gratuit donc prix_total=0)
            if acces.prix_total > 0:
                HotelConso.objects.create(
                    reservation=reservation, type_service='piscine',
                    nom=f'[Piscine] Entrée x{nb_total}',
                    quantite=1, prix_unitaire=acces.prix_total,
                )
            # Les consos sont déjà sur la chambre via ajouter_consommation
            # Générer reçu de dépôt
            lignes = [{'nom': f'Entrée piscine x{nb_total}', 'total': float(acces.prix_total)}]
            for c in acces.consommations.all():
                lignes.append({'nom': f'{c.produit} x{c.quantite}', 'total': float(c.get_total())})
            return JsonResponse({
                'success': True,
                'sur_chambre': True,
                'chambre_nom': f'Ch. {reservation.chambre.numero} — {reservation.client.nom_complet}',
                'lignes': lignes,
                'total': float(total),
                'message': f'Ajouté à la chambre {reservation.chambre.numero}'
            })

        # Mode PAIEMENT DIRECT : retirer les consos de la note chambre si hébergé
        if acces.reservation_hotel:
            from hotel.models import Consommation as HotelConso
            # Supprimer uniquement les consos de CET accès (identifiées par [Piscine#ID])
            HotelConso.objects.filter(
                reservation=acces.reservation_hotel,
                type_service='piscine',
                nom__startswith=f'[Piscine#{acces.id}]'
            ).delete()

        # Créer ticket facturation
        contenu = f'<div class="row"><span class="item-name">Entrée piscine x{nb_total}</span><span class="item-price">{int(acces.prix_total):,} F</span></div>'
        for c in acces.consommations.all():
            contenu += f'<div class="row"><span class="item-name">{c.produit} x{c.quantite}</span><span class="item-price">{int(c.get_total()):,} F</span></div>'

        ticket = Ticket.objects.create(
            numero=generate_ticket_numero(), module='piscine',
            montant_total=total, montant_paye=montant_recu,
            mode_paiement=mode_paiement, cree_par=request.user,
            contenu=contenu, imprime=True,
        )
        from django.template.loader import render_to_string
        ticket_html = render_to_string('facturation/ticket_print_thermal.html', {
            'ticket': ticket,
            'serveur': request.user.get_full_name() or request.user.username,
        })
        return JsonResponse({
            'success': True,
            'sur_chambre': False,
            'ticket_html': ticket_html,
            'total': float(total),
            'rendu': float(max(Decimal('0'), montant_recu - total)),
            'message': f'Sortie enregistrée — {acces.nom_client}'
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('piscine')
@require_POST
def configurer_tarifs(request):
    """Configurer les tarifs piscine."""
    try:
        data = json.loads(request.body)
        prix_adulte = Decimal(str(data.get('adulte', 0)))
        prix_enfant = Decimal(str(data.get('enfant', 0)))

        TarifPiscine.objects.update_or_create(
            type_tarif='adulte_visiteur',
            defaults={'prix_unitaire': prix_adulte}
        )
        TarifPiscine.objects.update_or_create(
            type_tarif='enfant_visiteur',
            defaults={'prix_unitaire': prix_enfant}
        )
        TarifPiscine.objects.update_or_create(
            type_tarif='adulte_heberge',
            defaults={'prix_unitaire': Decimal('0')}
        )
        TarifPiscine.objects.update_or_create(
            type_tarif='enfant_heberge',
            defaults={'prix_unitaire': Decimal('0')}
        )
        return JsonResponse({'success': True, 'message': 'Tarifs mis à jour'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('piscine')
def api_acces_detail(request, acces_id):
    """Détails d'un accès avec ses consommations."""
    acces = get_object_or_404(AccesPiscine, id=acces_id)
    consommations = [
        {'id': c.id, 'produit': c.produit, 'quantite': c.quantite,
         'prix': float(c.prix_unitaire), 'total': float(c.get_total())}
        for c in acces.consommations.all()
    ]
    total_conso = sum(c.get_total() for c in acces.consommations.all())
    return JsonResponse({
        'id': acces.id,
        'nom': acces.nom_client,
        'type': acces.get_type_client_display(),
        'nb': acces.nombre_personnes,
        'nb_adultes': acces.nb_adultes,
        'nb_enfants': acces.nb_enfants,
        'entree': float(acces.prix_total),
        'consommations': consommations,
        'total_conso': float(total_conso),
        'total': float(acces.prix_total + total_conso),
        'is_heberge': acces.type_client == 'heberge',
        'reservation_hotel_id': acces.reservation_hotel_id,
        'chambre_nom': (
            f'Ch. {acces.reservation_hotel.chambre.numero} — {acces.reservation_hotel.client.nom_complet}'
            if acces.reservation_hotel else None
        ),
    })


@require_module_access('piscine')
@require_POST
def modifier_consommation(request, conso_id):
    """Modifier la quantité d'une consommation existante."""
    try:
        from .models import ConsommationPiscine
        conso = get_object_or_404(ConsommationPiscine, id=conso_id)
        # Vérifier que l'accès n'est pas encore clôturé
        if conso.acces.date_sortie:
            return JsonResponse({'success': False, 'error': 'Accès déjà clôturé.'})
        data = json.loads(request.body)
        nouvelle_qty = int(data.get('quantite', 1))
        if nouvelle_qty < 1:
            return JsonResponse({'success': False, 'error': 'Quantité invalide.'})

        # Ajuster le stock bar si c'est une boisson
        from bar.models import BoissonBar, MouvementStockBar
        try:
            boisson = BoissonBar.objects.get(nom=conso.produit)
            diff = nouvelle_qty - conso.quantite
            if diff > 0 and boisson.quantite_stock < diff:
                return JsonResponse({'success': False, 'error': f'Stock insuffisant ({boisson.quantite_stock} disponible).'})
            boisson.quantite_stock = max(0, boisson.quantite_stock - diff)
            boisson.save()
            if diff != 0:
                MouvementStockBar.objects.create(
                    boisson=boisson, type_mouvement='sortie' if diff > 0 else 'entree',
                    quantite=abs(diff), commentaire=f'Modif piscine #{conso.acces.id}',
                    utilisateur=request.user
                )
        except BoissonBar.DoesNotExist:
            pass  # Plat, pas de stock à gérer

        conso.quantite = nouvelle_qty
        conso.save()
        total_conso = sum(c.get_total() for c in conso.acces.consommations.all())
        return JsonResponse({
            'success': True,
            'message': f'Quantité mise à jour : {conso.produit} x{nouvelle_qty}',
            'total_consommations': float(total_conso),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('piscine')
@require_POST
def supprimer_consommation(request, conso_id):
    """Supprimer une consommation et remettre le stock."""
    try:
        from .models import ConsommationPiscine
        conso = get_object_or_404(ConsommationPiscine, id=conso_id)
        if conso.acces.date_sortie:
            return JsonResponse({'success': False, 'error': 'Accès déjà clôturé.'})

        # Remettre le stock bar
        from bar.models import BoissonBar, MouvementStockBar
        try:
            boisson = BoissonBar.objects.get(nom=conso.produit)
            boisson.quantite_stock += conso.quantite
            boisson.save()
            MouvementStockBar.objects.create(
                boisson=boisson, type_mouvement='entree',
                quantite=conso.quantite, commentaire=f'Retour piscine #{conso.acces.id}',
                utilisateur=request.user
            )
        except BoissonBar.DoesNotExist:
            pass

        acces = conso.acces
        conso.delete()
        total_conso = sum(c.get_total() for c in acces.consommations.all())
        return JsonResponse({
            'success': True,
            'message': 'Article retiré',
            'total_consommations': float(total_conso),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
