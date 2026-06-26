from utils.permissions import require_module_access, user_has_access
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, F
from django.db import models as db_models
from .models import AccesPiscine, TarifPiscine, ConsommationPiscine
from decimal import Decimal
import json


def _json_piscine_access_required(view_func):
    """Décorateur pour endpoints AJAX piscine — retourne JSON 403 au lieu d'un redirect."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Session expirée — veuillez recharger la page.'}, status=403)
        if not user_has_access(request.user, 'piscine'):
            return JsonResponse({'success': False, 'error': 'Accès refusé au module piscine.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


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

    # Forfaits piscine disponibles + alertes stock
    from restaurant.models import Forfait
    forfaits_piscine = Forfait.objects.filter(module='piscine', disponible=True).prefetch_related('lignes__boisson', 'lignes__plat')
    forfaits_alertes = []
    forfaits_rupture_ids = set()  # IDs des forfaits en rupture de stock
    for _f in forfaits_piscine:
        _dispo, _pb = _verifier_stock_forfait(_f)
        if not _dispo:
            forfaits_alertes.append({'forfait': _f, 'problemes': _pb})
            forfaits_rupture_ids.add(_f.id)

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

    # Serveurs/Serveuses uniquement (groupe "Serveuse/Serveur") pour assignation commande
    personnel = User.objects.filter(
        is_active=True, groups__name='Serveuse/Serveur'
    ).order_by('first_name', 'last_name')

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
        'forfaits_piscine': forfaits_piscine,
        'forfaits_alertes': forfaits_alertes,
        'forfaits_rupture_ids': forfaits_rupture_ids,
        'personnel': personnel,
    }
    return render(request, 'piscine/index.html', context)


def _verifier_stock_forfait(forfait):
    """Vérifie que tous les articles d'un forfait sont en stock suffisant.
    Retourne (True, []) si OK, (False, [liste de problèmes]) sinon.
    Chaque problème : {'nom', 'type', 'stock', 'requis', 'detail'}
    """
    from restaurant.models import PlatMenu
    from cuisine.utils import check_stock_availability
    from bar.models import BoissonBar

    problemes = []
    for ligne in forfait.lignes.select_related('boisson', 'plat').all():
        if ligne.type_item == 'boisson' and ligne.boisson:
            b = ligne.boisson
            if b.quantite_stock < ligne.quantite:
                problemes.append({
                    'nom': ligne.nom_affiche,
                    'type': 'boisson',
                    'stock': float(b.quantite_stock),
                    'requis': float(ligne.quantite),
                    'detail': f"Stock disponible : {int(b.quantite_stock)}, requis : {int(ligne.quantite)}",
                })
        elif ligne.type_item == 'plat' and ligne.plat:
            try:
                plat_menu = PlatMenu.objects.filter(cuisine_plat_id=ligne.plat.id).first()
                if plat_menu:
                    ok, msg = check_stock_availability(plat_menu, ligne.quantite)
                    if not ok:
                        problemes.append({
                            'nom': ligne.nom_affiche,
                            'type': 'plat',
                            'stock': 0,
                            'requis': float(ligne.quantite),
                            'detail': msg,
                        })
            except Exception:
                pass
        elif ligne.type_item == 'autre':
            pass  # Libellé libre, pas de stock à vérifier
    return (len(problemes) == 0), problemes


def _generer_reference_entree(type_client, forfait=None, reservation=None):
    """Génère une référence professionnelle pour l'entrée piscine."""
    today = timezone.localdate()
    nb_today = AccesPiscine.objects.filter(date_entree__date=today).count() + 1
    if type_client == 'heberge' and reservation:
        return f"Ch.{reservation.chambre.numero} — {reservation.client.nom_complet}"
    if forfait:
        return f"VIP · {forfait.nom} — N°{nb_today:03d}"
    return f"Entrée N°{nb_today:03d}"


@require_POST
@_json_piscine_access_required
def enregistrer_entree(request):
    """Enregistrer une entrée piscine (ordinaire, VIP ou résident)."""
    try:
        data         = json.loads(request.body)
        type_client  = data.get('type_client', 'visiteur')
        nb_adultes   = int(data.get('nb_adultes', 1))
        nb_enfants   = int(data.get('nb_enfants', 0))
        forfait_id   = data.get('forfait_id')
        substitutions = {str(k): v for k, v in data.get('substitutions', {}).items()}

        if type_client != 'heberge' and nb_adultes < 1 and nb_enfants < 1:
            return JsonResponse({'success': False, 'error': 'Veuillez indiquer au moins 1 personne.'})

        # ── Forfait VIP ──────────────────────────────────────────────
        forfait = None
        if forfait_id:
            from restaurant.models import Forfait, PlatMenu
            from bar.models import BoissonBar
            from cuisine.utils import check_stock_availability
            try:
                forfait = Forfait.objects.prefetch_related('lignes__boisson', 'lignes__plat').get(
                    pk=forfait_id, module='piscine', disponible=True
                )
                prix_total = forfait.prix
                # Le forfait VIP couvre 1 adulte ; adultes suppl. et enfants au tarif standard
                extras_adultes = max(0, nb_adultes - 1)
                if extras_adultes > 0 or nb_enfants > 0:
                    t_adulte_vip = TarifPiscine.objects.filter(type_tarif='adulte_visiteur').first()
                    t_enfant_vip = TarifPiscine.objects.filter(type_tarif='enfant_visiteur').first()
                    if extras_adultes > 0 and t_adulte_vip:
                        prix_total += t_adulte_vip.prix_unitaire * extras_adultes
                    if nb_enfants > 0 and t_enfant_vip:
                        prix_total += t_enfant_vip.prix_unitaire * nb_enfants
            except Forfait.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Forfait VIP introuvable ou indisponible.'})

            # Validation stock article par article (original OU substitut)
            problemes_final = []
            for ligne in forfait.lignes.select_related('boisson', 'plat').all():
                sub = substitutions.get(str(ligne.id))
                if sub:
                    # Valider le substitut
                    if sub['type'] == 'boisson':
                        try:
                            b_sub = BoissonBar.objects.get(id=sub['id'])
                            if b_sub.quantite_stock < ligne.quantite:
                                problemes_final.append(
                                    f"Substitut « {b_sub.nom} » insuffisant "
                                    f"(stock : {int(b_sub.quantite_stock)}, requis : {int(ligne.quantite)})"
                                )
                        except BoissonBar.DoesNotExist:
                            problemes_final.append(f"Substitut boisson introuvable (id={sub['id']})")
                    elif sub['type'] == 'plat':
                        try:
                            plat_sub = PlatMenu.objects.get(id=sub['id'])
                            ok, msg = check_stock_availability(plat_sub, ligne.quantite)
                            if not ok:
                                problemes_final.append(f"Substitut « {plat_sub.nom} » : {msg}")
                        except PlatMenu.DoesNotExist:
                            problemes_final.append(f"Substitut plat introuvable (id={sub['id']})")
                else:
                    # Valider l'article original
                    if ligne.type_item == 'boisson' and ligne.boisson:
                        b = ligne.boisson
                        if b.quantite_stock < ligne.quantite:
                            problemes_final.append(
                                f"« {ligne.nom_affiche} » en rupture "
                                f"(stock : {int(b.quantite_stock)}, requis : {int(ligne.quantite)})"
                            )
                    elif ligne.type_item == 'plat' and ligne.plat:
                        try:
                            plat_menu = PlatMenu.objects.filter(cuisine_plat_id=ligne.plat.id).first()
                            if plat_menu:
                                ok, msg = check_stock_availability(plat_menu, ligne.quantite)
                                if not ok:
                                    problemes_final.append(f"« {ligne.nom_affiche} » : {msg}")
                        except Exception:
                            pass

            if problemes_final:
                return JsonResponse({
                    'success': False,
                    'error': 'Stock insuffisant — ' + ' | '.join(problemes_final),
                })

        # ── Tarif ordinaire ──────────────────────────────────────────
        elif type_client == 'heberge':
            prix_total = Decimal('0')
        else:
            t_adulte = TarifPiscine.objects.filter(type_tarif='adulte_visiteur').first()
            t_enfant = TarifPiscine.objects.filter(type_tarif='enfant_visiteur').first()
            if not t_adulte:
                return JsonResponse({'success': False, 'error': 'Tarif adulte non configuré.'})
            prix_total = (
                (t_adulte.prix_unitaire * nb_adultes if nb_adultes else Decimal('0')) +
                (t_enfant.prix_unitaire * nb_enfants if t_enfant and nb_enfants else Decimal('0'))
            )

        # ── Réservation hôtel ─────────────────────────────────────────
        reservation_hotel = None
        reservation_id = data.get('reservation_id')
        if type_client == 'heberge' and reservation_id:
            from hotel.models import Reservation as HotelReservation
            try:
                reservation_hotel = HotelReservation.objects.get(id=reservation_id, statut='en_cours')
            except HotelReservation.DoesNotExist:
                pass

        # ── Référence automatique (pas de saisie nom client) ──────────
        nom_client = _generer_reference_entree(type_client, forfait=forfait, reservation=reservation_hotel)

        # ── Créer l'accès ─────────────────────────────────────────────
        acces = AccesPiscine.objects.create(
            nom_client=nom_client,
            type_client=type_client,
            nb_adultes=nb_adultes,
            nb_enfants=nb_enfants,
            prix_total=prix_total,
            enregistre_par=request.user,
            reservation_hotel=reservation_hotel,
            forfait=forfait,
        )

        # ── Articles inclus dans le forfait VIP ───────────────────────
        if forfait:
            from bar.models import BoissonBar, MouvementStockBar
            from restaurant.models import PlatMenu
            from cuisine.utils import process_stock_movement
            for ligne in forfait.lignes.select_related('boisson', 'plat').all():
                sub = substitutions.get(str(ligne.id))

                if sub:
                    # ── Article de substitution ──
                    if sub['type'] == 'boisson':
                        b_sub = BoissonBar.objects.get(id=sub['id'])
                        nom_article = f"{b_sub.nom} (remplace {ligne.nom_affiche})"
                        ConsommationPiscine.objects.create(
                            acces=acces, produit=nom_article,
                            quantite=ligne.quantite, prix_unitaire=Decimal('0'), inclus_forfait=True,
                        )
                        MouvementStockBar.objects.create(
                            boisson=b_sub, type_mouvement='sortie', quantite=ligne.quantite,
                            commentaire=f'Menu VIP #{acces.id} (substitut)', utilisateur=request.user,
                        )
                    elif sub['type'] == 'plat':
                        plat_sub = PlatMenu.objects.get(id=sub['id'])
                        nom_article = f"{plat_sub.nom} (remplace {ligne.nom_affiche})"
                        ConsommationPiscine.objects.create(
                            acces=acces, produit=nom_article,
                            quantite=ligne.quantite, prix_unitaire=Decimal('0'), inclus_forfait=True,
                        )
                        process_stock_movement(plat_sub, ligne.quantite, 'sortie', request.user, f'Menu VIP #{acces.id} (substitut)')
                else:
                    # ── Article original ──
                    nom_article = ligne.nom_affiche
                    ConsommationPiscine.objects.create(
                        acces=acces, produit=nom_article,
                        quantite=ligne.quantite, prix_unitaire=Decimal('0'), inclus_forfait=True,
                    )
                    if ligne.type_item == 'boisson' and ligne.boisson:
                        b = ligne.boisson
                        MouvementStockBar.objects.create(
                            boisson=b, type_mouvement='sortie', quantite=ligne.quantite,
                            commentaire=f'Menu VIP piscine #{acces.id}', utilisateur=request.user,
                        )
                    elif ligne.type_item == 'plat' and ligne.plat:
                        try:
                            plat_menu = PlatMenu.objects.filter(cuisine_plat_id=ligne.plat.id).first()
                            if plat_menu:
                                process_stock_movement(plat_menu, ligne.quantite, 'sortie', request.user, f'Menu VIP #{acces.id}')
                        except Exception:
                            pass

        return JsonResponse({
            'success': True,
            'acces_id': acces.id,
            'nom': acces.nom_client,
            'reference': acces.nom_client,
            'type': acces.get_type_client_display(),
            'forfait': forfait.nom if forfait else None,
            'prix': float(prix_total),
            'message': f"Entrée enregistrée — {acces.nom_client}"
        })
    except Exception as e:
        import traceback; traceback.print_exc()
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
        serveur_id   = data.get('serveur_id')
        serveur_obj  = None
        if serveur_id:
            try:
                serveur_obj = User.objects.get(pk=serveur_id, is_active=True)
            except User.DoesNotExist:
                pass

        if type_article == 'boisson':
            from bar.models import BoissonBar, MouvementStockBar
            boisson = get_object_or_404(BoissonBar, id=article_id)
            if boisson.quantite_stock < quantite:
                return JsonResponse({'success': False, 'error': f'Stock insuffisant pour {boisson.nom} (reste : {boisson.quantite_stock})'})
            ConsommationPiscine.objects.create(
                acces=acces,
                produit=boisson.nom,
                quantite=quantite,
                prix_unitaire=boisson.prix,
                serveur=serveur_obj,
            )
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
            from cuisine.utils import check_stock_availability, process_stock_movement
            plat = get_object_or_404(PlatMenu, id=article_id)
            # Vérification stock cuisine
            ok, msg = check_stock_availability(plat, quantite)
            if not ok:
                return JsonResponse({'success': False, 'error': f'Stock insuffisant — {msg}'})
            ConsommationPiscine.objects.create(
                acces=acces,
                produit=plat.nom,
                quantite=quantite,
                prix_unitaire=plat.prix,
                serveur=serveur_obj,
            )
            # Déduire le stock cuisine
            process_stock_movement(plat, quantite, 'sortie', request.user, f'Piscine #{acces.id}')
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

        # Validation montant pour tout paiement direct
        if not sur_chambre and montant_recu < total:
            return JsonResponse({'success': False, 'error': f'Montant insuffisant. Total : {int(total)} F'})

        # Marquer sortie
        acces.date_sortie = timezone.now()
        acces.save()

        nb_total = acces.nb_adultes + acces.nb_enfants

        # Build itemized entry lines (VIP broken into forfait + extras)
        if acces.forfait:
            from piscine.models import TarifPiscine
            t_adulte = TarifPiscine.objects.filter(type_tarif='adulte_visiteur').first()
            t_enfant = TarifPiscine.objects.filter(type_tarif='enfant_visiteur').first()
            extras_adultes = max(0, acces.nb_adultes - 1)
            label_entree = f'Menu VIP {acces.forfait.nom}'
            lignes_entree = [{'nom': label_entree, 'total': float(acces.forfait.prix)}]
            if extras_adultes > 0 and t_adulte:
                lignes_entree.append({'nom': f'Entrée Adulte × {extras_adultes}', 'total': float(t_adulte.prix_unitaire * extras_adultes)})
            if acces.nb_enfants > 0 and t_enfant:
                lignes_entree.append({'nom': f'Entrée Enfant × {acces.nb_enfants}', 'total': float(t_enfant.prix_unitaire * acces.nb_enfants)})
        else:
            label_entree = f'Entrée piscine x{nb_total}'
            lignes_entree = [{'nom': label_entree, 'total': float(acces.prix_total)}]

        # Mode CHAMBRE : ajouter les consos à la réservation hôtel sans créer ticket séparé
        if sur_chambre and acces.reservation_hotel:
            reservation = acces.reservation_hotel
            from hotel.models import Consommation as HotelConso
            # Ajouter entrée si payante (hébergé gratuit donc prix_total=0)
            if acces.prix_total > 0:
                HotelConso.objects.create(
                    reservation=reservation, type_service='piscine',
                    nom=f'[Piscine] {label_entree}',
                    quantite=1, prix_unitaire=acces.prix_total,
                )
            # Les consos sont déjà sur la chambre via ajouter_consommation
            # Générer reçu de dépôt
            lignes = list(lignes_entree)
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
        contenu = ''
        for le in lignes_entree:
            contenu += f'<div class="row"><span class="item-name">{le["nom"]}</span><span class="item-price">{int(le["total"]):,} F</span></div>'
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
def check_forfait_dispo(request, forfait_id):
    """Vérifie la disponibilité de stock pour un forfait VIP (appel AJAX)."""
    from restaurant.models import Forfait
    try:
        forfait = Forfait.objects.prefetch_related('lignes__boisson', 'lignes__plat').get(
            pk=forfait_id, module='piscine', disponible=True
        )
    except Forfait.DoesNotExist:
        return JsonResponse({'disponible': False, 'problemes': [{'nom': 'Forfait', 'detail': 'Introuvable ou désactivé.'}]})

    dispo, problemes = _verifier_stock_forfait(forfait)
    problemes_noms = {p['nom'] for p in problemes}
    lignes_statut = []
    for ligne in forfait.lignes.select_related('boisson', 'plat').all():
        nom = ligne.nom_affiche
        ok = nom not in problemes_noms
        stock_dispo = None
        if ligne.type_item == 'boisson' and ligne.boisson:
            stock_dispo = float(ligne.boisson.quantite_stock)
        lignes_statut.append({
            'id': ligne.id,
            'nom': nom,
            'type': ligne.type_item,
            'quantite': float(ligne.quantite),
            'ok': ok,
            'stock_dispo': stock_dispo,
            'detail': next((p['detail'] for p in problemes if p['nom'] == nom), ''),
        })
    return JsonResponse({
        'disponible': dispo,
        'lignes': lignes_statut,
        'problemes': problemes,
    })


@require_module_access('piscine')
def ticket_entree(request, acces_id):
    """Affiche le ticket d'entrée piscine (impression immédiate)."""
    acces = get_object_or_404(AccesPiscine, id=acces_id)
    # Extraire le numéro d'ordre depuis nom_client (ex: "Entrée N°003" → "003")
    import re
    m = re.search(r'N°\s*(\d+)', acces.nom_client)
    if m:
        numero_affiche = 'N°' + m.group(1)
    elif acces.type_client == 'heberge' and acces.reservation_hotel:
        numero_affiche = 'Ch.' + str(acces.reservation_hotel.chambre.numero)
    else:
        numero_affiche = 'N°' + str(acces.pk).zfill(3)
    return render(request, 'piscine/ticket_entree_piscine.html', {
        'acces': acces,
        'numero_affiche': numero_affiche,
    })


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
         'prix': float(c.prix_unitaire), 'total': float(c.get_total()),
         'inclus_forfait': c.inclus_forfait,
         'serveur': c.serveur.get_full_name() or c.serveur.username if c.serveur else None}
        for c in acces.consommations.select_related('serveur').all()
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
        'forfait_nom': acces.forfait.nom if acces.forfait else None,
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
