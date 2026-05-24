from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from utils.permissions import get_accessible_modules
from datetime import timedelta


def _get_dashboard_stats(user, modules):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    stats = {
        'date_ref': None,
        'ca_jour': 0, 'ca_hier': 0, 'ca_mois': 0,
        'nb_tickets_jour': 0,
        'taux_occupation': 0, 'chambres_occupees': 0, 'total_chambres': 0,
        'reservations_actives': 0, 'reservations_attente': 0,
        'alertes_stock': 0,
        'caisse_ouverte': False, 'caisse_type': '',
        'tickets_recents': [],
        'ca_par_module': {},
        'ca_7_jours': [],
        'piscine_entrees': 0,
        'espaces_reservations': 0,
        'commandes_restaurant': 0,
    }

    try:
        from facturation.models import Ticket
        tickets_jour = Ticket.objects.filter(date_creation__date=today)
        tickets_hier = Ticket.objects.filter(date_creation__date=yesterday)
        tickets_mois = Ticket.objects.filter(
            date_creation__month=today.month,
            date_creation__year=today.year
        )

        stats['ca_jour'] = int(tickets_jour.aggregate(s=Sum('montant_total'))['s'] or 0)
        stats['ca_hier'] = int(tickets_hier.aggregate(s=Sum('montant_total'))['s'] or 0)
        stats['ca_mois'] = int(tickets_mois.aggregate(s=Sum('montant_total'))['s'] or 0)
        stats['nb_tickets_jour'] = tickets_jour.count()

        # Si pas de tickets aujourd'hui → utiliser la dernière journée active
        tickets_module_ref = tickets_jour
        stats['date_ref'] = today
        if not tickets_jour.exists():
            last = Ticket.objects.order_by('-date_creation').first()
            if last:
                last_date = last.date_creation.date()
                tickets_module_ref = Ticket.objects.filter(date_creation__date=last_date)
                stats['date_ref'] = last_date
                stats['ca_jour'] = int(tickets_module_ref.aggregate(s=Sum('montant_total'))['s'] or 0)
                stats['nb_tickets_jour'] = tickets_module_ref.count()

        # CA par module
        for mod, label in [('hotel','Hôtel'),('restaurant','Restaurant'),('cave','Cave'),('piscine','Piscine'),('espace','Espaces')]:
            ca = tickets_module_ref.filter(module__startswith=mod).aggregate(s=Sum('montant_total'))['s'] or 0
            if ca: stats['ca_par_module'][label] = int(ca)

        # CA 7 derniers jours
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            ca = Ticket.objects.filter(date_creation__date=d).aggregate(s=Sum('montant_total'))['s'] or 0
            stats['ca_7_jours'].append({'jour': d.strftime('%a'), 'ca': int(ca)})

        # Tickets récents
        stats['tickets_recents'] = list(
            tickets_jour.select_related('client','cree_par').order_by('-date_creation')[:8].values(
                'numero','module','montant_total','mode_paiement',
                'date_creation','cree_par__first_name','cree_par__last_name','cree_par__username'
            )
        )
    except Exception:
        pass

    # Hôtel
    if 'hotel' in modules or '*' in modules:
        try:
            from hotel.models import Chambre, Reservation
            stats['total_chambres'] = Chambre.objects.count()
            stats['chambres_occupees'] = Chambre.objects.filter(statut='occupee').count()
            stats['taux_occupation'] = round(
                (stats['chambres_occupees'] / stats['total_chambres'] * 100)
                if stats['total_chambres'] else 0
            )
            stats['reservations_actives'] = Reservation.objects.filter(statut='en_cours').count()
            stats['reservations_attente'] = Reservation.objects.filter(statut__in=['en_attente','confirmee']).count()
        except Exception:
            pass

    # Cuisine stock
    if 'cuisine' in modules or '*' in modules:
        try:
            from cuisine.models import Ingredient
            stats['alertes_stock'] = Ingredient.objects.filter(quantite_stock__lte=5).count()
        except Exception:
            pass

    # Caisse ouverte
    try:
        from caisse.models import CaisseSession
        # La caisse centrale est ouverte uniquement si une session de type 'centrale' existe
        session_centrale = CaisseSession.objects.filter(is_open=True, type_caisse='centrale').first()
        session_any = CaisseSession.objects.filter(is_open=True).first()
        stats['caisse_ouverte'] = session_centrale is not None
        stats['caisse_type'] = session_centrale.get_type_caisse_display() if session_centrale else (
            session_any.get_type_caisse_display() if session_any else ''
        )
    except Exception:
        pass

    # Piscine entrées du jour
    try:
        from facturation.models import Ticket
        stats['piscine_entrees'] = Ticket.objects.filter(
            date_creation__date=today, module='piscine'
        ).count()
    except Exception:
        pass

    # Espaces réservations actives
    try:
        from espaces_evenementiels.models import ReservationEspace
        stats['espaces_reservations'] = ReservationEspace.objects.filter(statut='confirmee').count()
    except Exception:
        pass

    # Restaurant commandes en cours
    try:
        from restaurant.models import Commande
        stats['commandes_restaurant'] = Commande.objects.filter(statut='en_attente').count()
    except Exception:
        pass

    return stats


@login_required
def dashboard_view(request):
    today = timezone.now().date()
    modules = get_accessible_modules(request.user)
    stats = _get_dashboard_stats(request.user, modules)

    context = {
        **stats,
        'date_ref': stats.get('date_ref', today),
        'user': request.user,
        'today': today,
        'accessible_modules': modules,
        'variation': f"+{round(((stats["ca_jour"]-stats["ca_hier"])/stats["ca_hier"]*100) if stats["ca_hier"] else 0)}%",
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def direction_view(request):
    """Vue consolidée Direction — stocks, mouvements et stats de tous les modules."""
    from utils.permissions import _is_manager
    from django.contrib import messages
    if not (_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "Accès réservé à la Direction et aux Managers.")
        return redirect('dashboard:index')

    today = timezone.now().date()
    modules = get_accessible_modules(request.user)
    stats = _get_dashboard_stats(request.user, modules)

    bar_ruptures, bar_alertes = 0, 0
    cuisine_ruptures, cuisine_alertes = 0, 0
    mouvements_combines = []

    try:
        from bar.models import BoissonBar, MouvementStockBar
        bar_qs = BoissonBar.objects.filter(statut='actif')
        bar_ruptures = sum(1 for a in bar_qs if a.est_en_rupture())
        bar_alertes  = sum(1 for a in bar_qs if a.est_stock_bas())
        for m in MouvementStockBar.objects.select_related('boisson', 'utilisateur').order_by('-date')[:30]:
            mouvements_combines.append({
                'source': 'cave', 'nom': m.boisson.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': m.quantite, 'date': m.date,
                'user': m.utilisateur, 'commentaire': m.commentaire or '',
            })
    except Exception:
        pass

    try:
        from cuisine.models import Ingredient, MouvementStockCuisine
        cuisine_qs = Ingredient.objects.filter(statut=True)
        cuisine_ruptures = sum(1 for i in cuisine_qs if i.est_en_rupture())
        cuisine_alertes  = sum(1 for i in cuisine_qs if i.est_stock_bas())
        for m in MouvementStockCuisine.objects.select_related('ingredient', 'utilisateur').order_by('-date')[:30]:
            mouvements_combines.append({
                'source': 'cuisine', 'nom': m.ingredient.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': m.quantite, 'date': m.date,
                'user': m.utilisateur, 'commentaire': m.commentaire or '',
            })
    except Exception:
        pass

    mouvements_combines.sort(key=lambda x: x['date'], reverse=True)

    # ── Fond de caisse & sessions ──────────────────────────────
    sessions_jour = []
    stats_caisse_jour = {}
    solde_veille_dir = 0
    try:
        from caisse.models import CaisseSession
        from caisse.views import get_stats_jour, get_solde_veille
        today_local = timezone.localdate()
        sessions_jour = list(
            CaisseSession.objects.filter(date_session=today_local)
            .select_related('user').order_by('-opened_at')
        )
        stats_caisse_jour = get_stats_jour(today_local)
        solde_veille_dir, _ = get_solde_veille()
    except Exception:
        pass

    context = {
        **stats,
        'today': today,
        'accessible_modules': modules,
        'bar_ruptures': bar_ruptures,
        'bar_alertes': bar_alertes,
        'cuisine_ruptures': cuisine_ruptures,
        'cuisine_alertes': cuisine_alertes,
        'mouvements_combines': mouvements_combines[:40],
        'sessions_jour': sessions_jour,
        'stats_caisse_jour': stats_caisse_jour,
        'solde_veille_dir': solde_veille_dir,
    }
    return render(request, 'dashboard/direction.html', context)


@login_required
def api_stats(request):
    """API temps réel — appelée toutes les 30s par le dashboard."""
    modules = get_accessible_modules(request.user)
    stats = _get_dashboard_stats(request.user, modules)
    # Retirer les objets non-sérialisables
    stats.pop('tickets_recents', None)
    return JsonResponse(stats)
