from utils.permissions import require_module_access
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum
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
    recette_jour   = AccesPiscine.objects.filter(
        date_entree__date=today
    ).aggregate(s=Sum('prix_total'))['s'] or 0

    # Tarifs
    tarif_visiteur = TarifPiscine.objects.filter(type_client='visiteur').first()
    tarif_heberge  = TarifPiscine.objects.filter(type_client='heberge').first()

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
        'tarif_visiteur': tarif_visiteur,
        'tarif_heberge': tarif_heberge,
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
        type_client   = data.get('type_client', 'visiteur')
        nom_client    = data.get('nom_client', '').strip()
        nb_personnes  = int(data.get('nombre_personnes', 1))
        chambre_num   = data.get('chambre', '')

        if not nom_client:
            return JsonResponse({'success': False, 'error': 'Nom du client requis'})

        # Calcul prix
        if type_client == 'heberge':
            prix_total = Decimal('0')  # Gratuit pour résidents
        else:
            tarif = TarifPiscine.objects.filter(type_client='visiteur').first()
            if not tarif:
                return JsonResponse({'success': False, 'error': 'Tarif visiteur non configuré. Veuillez le définir dans les paramètres.'})
            prix_total = tarif.prix_unitaire * nb_personnes

        acces = AccesPiscine.objects.create(
            nom_client=nom_client,
            type_client=type_client,
            nombre_personnes=nb_personnes,
            prix_total=prix_total,
            enregistre_par=request.user,
        )

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

        # Total = entrée + consommations
        total_conso = sum(c.get_total() for c in acces.consommations.all())
        total       = acces.prix_total + total_conso

        if montant_recu < total and acces.type_client == 'visiteur':
            return JsonResponse({'success': False, 'error': f'Montant insuffisant. Total : {int(total)} F'})

        # Marquer sortie
        acces.date_sortie = timezone.now()
        acces.save()

        # Générer contenu ticket
        contenu = f"""
        <div class="row"><span class="item-name">Entrée piscine x{acces.nombre_personnes}</span>
        <span class="item-price">{int(acces.prix_total):,} F</span></div>
        """
        for c in acces.consommations.all():
            contenu += f"""
        <div class="row"><span class="item-name">{c.produit} x{c.quantite}</span>
        <span class="item-price">{int(c.get_total()):,} F</span></div>
            """

        # Créer ticket
        ticket = Ticket.objects.create(
            numero=generate_ticket_numero(),
            module='piscine',
            montant_total=total,
            montant_paye=montant_recu,
            mode_paiement=mode_paiement,
            cree_par=request.user,
            contenu=contenu,
            imprime=True,
        )

        from django.template.loader import render_to_string
        ticket_html = render_to_string('facturation/ticket_print_thermal.html', {
            'ticket': ticket,
            'serveur': request.user.get_full_name() or request.user.username,
        })

        return JsonResponse({
            'success': True,
            'ticket_html': ticket_html,
            'total': float(total),
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
        prix_visiteur = Decimal(str(data.get('visiteur', 0)))

        TarifPiscine.objects.update_or_create(
            type_client='visiteur',
            defaults={'prix_unitaire': prix_visiteur}
        )
        TarifPiscine.objects.update_or_create(
            type_client='heberge',
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
        {'produit': c.produit, 'quantite': c.quantite,
         'prix': float(c.prix_unitaire), 'total': float(c.get_total())}
        for c in acces.consommations.all()
    ]
    total_conso = sum(c.get_total() for c in acces.consommations.all())
    return JsonResponse({
        'id': acces.id,
        'nom': acces.nom_client,
        'type': acces.get_type_client_display(),
        'nb': acces.nombre_personnes,
        'entree': acces.prix_total,
        'consommations': consommations,
        'total_conso': float(total_conso),
        'total': float(acces.prix_total + total_conso),
    })
