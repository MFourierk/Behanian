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
    from datetime import date as date_type
    if not (_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "Accès réservé à la Direction et aux Managers.")
        return redirect('dashboard:index')

    today = timezone.now().date()
    modules = get_accessible_modules(request.user)
    stats = _get_dashboard_stats(request.user, modules)

    # Filtre date mouvements — défaut = aujourd'hui
    active_tab = request.GET.get('tab', 'global')
    date_mvt_str = request.GET.get('date_mvt', today.isoformat())
    try:
        date_mvt = date_type.fromisoformat(date_mvt_str)
    except ValueError:
        date_mvt = today

    bar_ruptures, bar_alertes = 0, 0
    cuisine_ruptures, cuisine_alertes = 0, 0
    mouvements_combines = []

    try:
        from bar.models import BoissonBar, MouvementStockBar
        bar_qs = BoissonBar.objects.filter(statut='actif')
        bar_ruptures = sum(1 for a in bar_qs if a.est_en_rupture)
        bar_alertes  = sum(1 for a in bar_qs if a.est_stock_bas)
        qs_bar = MouvementStockBar.objects.filter(date__date=date_mvt).select_related('boisson', 'utilisateur').order_by('-date')
        for m in qs_bar:
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
        cuisine_ruptures = sum(1 for i in cuisine_qs if i.est_en_rupture)
        cuisine_alertes  = sum(1 for i in cuisine_qs if i.est_stock_bas)
        qs_cuisine = MouvementStockCuisine.objects.filter(date__date=date_mvt).select_related('ingredient', 'utilisateur').order_by('-date')
        for m in qs_cuisine:
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
        'mouvements_combines': mouvements_combines,
        'sessions_jour': sessions_jour,
        'stats_caisse_jour': stats_caisse_jour,
        'solde_veille_dir': solde_veille_dir,
        'active_tab': active_tab,
        'date_mvt': date_mvt.isoformat() if date_mvt else '',
    }
    return render(request, 'dashboard/direction.html', context)


@login_required
def mouvements_print(request):
    """Page d'impression des mouvements de stock — modèle print_base.html."""
    from utils.permissions import _is_manager
    from django.contrib import messages
    from datetime import date as date_type

    if not (_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "Accès réservé à la Direction.")
        return redirect('dashboard:index')

    date_mvt_str = request.GET.get('date_mvt', timezone.now().date().isoformat())
    try:
        date_mvt = date_type.fromisoformat(date_mvt_str)
    except ValueError:
        date_mvt = timezone.now().date()

    mouvements = []
    try:
        from bar.models import MouvementStockBar
        for m in MouvementStockBar.objects.filter(date__date=date_mvt).select_related('boisson', 'utilisateur').order_by('-date'):
            mouvements.append({
                'source': 'cave', 'source_label': 'Cave & Bar',
                'nom': m.boisson.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': m.quantite, 'unite': 'unité(s)',
                'date': m.date,
                'user': m.utilisateur.get_full_name() or m.utilisateur.username if m.utilisateur else '—',
                'commentaire': m.commentaire or '—',
            })
    except Exception:
        pass

    try:
        from cuisine.models import MouvementStockCuisine
        for m in MouvementStockCuisine.objects.filter(date__date=date_mvt).select_related('ingredient', 'utilisateur').order_by('-date'):
            mouvements.append({
                'source': 'cuisine', 'source_label': 'Cuisine',
                'nom': m.ingredient.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': m.quantite, 'unite': str(m.ingredient.unite_stock) if m.ingredient.unite_stock else '—',
                'date': m.date,
                'user': m.utilisateur.get_full_name() or m.utilisateur.username if m.utilisateur else '—',
                'commentaire': m.commentaire or '—',
            })
    except Exception:
        pass

    mouvements.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'dashboard/mouvements_print.html', {
        'date_mvt': date_mvt,
        'mouvements': mouvements,
        'nb_cave': sum(1 for m in mouvements if m['source'] == 'cave'),
        'nb_cuisine': sum(1 for m in mouvements if m['source'] == 'cuisine'),
        'generated_at': timezone.now(),
    })


@login_required
def mouvements_excel(request):
    """Export Excel : mouvements de stock globaux (Cave + Cuisine) — Vue Direction"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from utils.permissions import _is_manager
    from datetime import date as date_type

    if not (_is_manager(request.user) or request.user.is_superuser):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    date_mvt_str = request.GET.get('date_mvt', timezone.now().date().isoformat())
    try:
        date_mvt = date_type.fromisoformat(date_mvt_str)
    except ValueError:
        date_mvt = timezone.now().date()

    mouvements = []
    try:
        from bar.models import MouvementStockBar
        for m in MouvementStockBar.objects.filter(date__date=date_mvt).select_related('boisson', 'utilisateur').order_by('-date'):
            mouvements.append({
                'source': 'Cave & Bar', 'nom': m.boisson.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': float(m.quantite), 'unite': 'unité(s)',
                'date': m.date,
                'user': m.utilisateur.get_full_name() or m.utilisateur.username if m.utilisateur else '—',
                'commentaire': m.commentaire or '',
            })
    except Exception:
        pass
    try:
        from cuisine.models import MouvementStockCuisine
        for m in MouvementStockCuisine.objects.filter(date__date=date_mvt).select_related('ingredient', 'utilisateur').order_by('-date'):
            mouvements.append({
                'source': 'Cuisine', 'nom': m.ingredient.nom,
                'type': m.get_type_mouvement_display(), 'type_code': m.type_mouvement,
                'quantite': float(m.quantite),
                'unite': str(m.ingredient.unite_stock) if m.ingredient.unite_stock else '—',
                'date': m.date,
                'user': m.utilisateur.get_full_name() or m.utilisateur.username if m.utilisateur else '—',
                'commentaire': m.commentaire or '',
            })
    except Exception:
        pass
    mouvements.sort(key=lambda x: x['date'], reverse=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mouvements"

    hf  = PatternFill("solid", fgColor="1a2535")
    hft = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
    tf  = Font(name='Calibri', bold=True, size=14, color='1a2535')
    bf  = Font(name='Calibri', bold=True, size=10)
    nf  = Font(name='Calibri', size=10)
    th  = Side(border_style="thin", color="d4dce8")
    bd  = Border(left=th, right=th, top=th, bottom=th)
    ct  = Alignment(horizontal='center', vertical='center')
    rt  = Alignment(horizontal='right', vertical='center')

    NC = 9
    ws.merge_cells(f'A1:{get_column_letter(NC)}1')
    ws['A1'] = f"MOUVEMENTS DE STOCK — {date_mvt.strftime('%d/%m/%Y').upper()} — COMPLEXE BEHANIAN"
    ws['A1'].font = tf; ws['A1'].alignment = ct

    ws.merge_cells(f'A2:{get_column_letter(NC)}2')
    ws['A2'] = f"{len(mouvements)} mouvement(s) — Édité le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
    ws['A2'].font = Font(name='Calibri', size=10, color='7a8b9c', italic=True)
    ws['A2'].alignment = ct

    ws.append([])
    headers = ['#', 'Module', 'Article', 'Type de mouvement', 'Quantité', 'Unité', 'Heure', 'Utilisateur', 'Commentaire']
    ws.append(headers)
    rh = ws.max_row
    for col in range(1, NC + 1):
        c = ws.cell(row=rh, column=col)
        c.fill = hf; c.font = hft; c.alignment = ct; c.border = bd

    cave_fill = PatternFill("solid", fgColor="ede9fe")
    cuis_fill = PatternFill("solid", fgColor="fff7ed")
    for i, m in enumerate(mouvements, 1):
        ws.append([
            i, m['source'], m['nom'], m['type'],
            m['quantite'], m['unite'],
            m['date'].strftime('%H:%M'), m['user'], m['commentaire'],
        ])
        rw = ws.max_row
        row_fill = cave_fill if m['source'] == 'Cave & Bar' else cuis_fill
        for col in range(1, NC + 1):
            c = ws.cell(row=rw, column=col)
            c.font = bf if col in (3, 5) else nf
            c.border = bd
            c.fill = row_fill
            c.alignment = rt if col == 5 else (ct if col in (1, 2, 7) else Alignment(vertical='center'))

    ws.append([])
    tr = ws.max_row + 1
    ws.cell(row=tr, column=4, value='TOTAL').font = Font(name='Calibri', bold=True)
    ws.cell(row=tr, column=5, value=len(mouvements)).font = Font(name='Calibri', bold=True, size=11)

    for col, w in enumerate([5, 12, 28, 20, 10, 9, 8, 18, 30], 1):
        ws.column_dimensions[get_column_letter(col)].width = w

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Mouvements_{date_mvt.strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


@login_required
def api_stats(request):
    """API temps réel — appelée toutes les 30s par le dashboard."""
    modules = get_accessible_modules(request.user)
    stats = _get_dashboard_stats(request.user, modules)
    # Retirer les objets non-sérialisables
    stats.pop('tickets_recents', None)
    return JsonResponse(stats)
