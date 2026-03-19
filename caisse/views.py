from utils.permissions import require_module_access, require_manager, GROUPE_MANAGER_GENERAL, GROUPE_CAISSIER_PRINCIPAL
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import CaisseSession
from facturation.models import Ticket


def get_stats_caisse(date=None, user=None):
    """Calcule les statistiques de caisse pour une date donnée."""
    if date is None:
        date = timezone.now().date()

    tickets = Ticket.objects.filter(date_creation__date=date)

    # Filtrer par utilisateur si caissier
    if user and not user.groups.filter(name=GROUPE_MANAGER_GENERAL).exists() and not user.is_superuser:
        tickets = tickets.filter(cree_par=user)

    total         = tickets.aggregate(s=Sum('montant_total'))['s'] or 0
    nb_tickets    = tickets.count()
    especes       = tickets.filter(mode_paiement='especes').aggregate(s=Sum('montant_total'))['s'] or 0
    mobile        = tickets.filter(mode_paiement__in=['mobile_money','orange_money','wave','moov_money','mtn_money']).aggregate(s=Sum('montant_total'))['s'] or 0
    carte         = tickets.filter(mode_paiement='carte_bancaire').aggregate(s=Sum('montant_total'))['s'] or 0
    virement      = tickets.filter(mode_paiement='virement').aggregate(s=Sum('montant_total'))['s'] or 0

    # Par module
    hotel_total      = tickets.filter(module='hotel').aggregate(s=Sum('montant_total'))['s'] or 0
    restaurant_total = tickets.filter(module='restaurant').aggregate(s=Sum('montant_total'))['s'] or 0
    bar_total        = tickets.filter(module='bar').aggregate(s=Sum('montant_total'))['s'] or 0
    piscine_total    = tickets.filter(module='piscine').aggregate(s=Sum('montant_total'))['s'] or 0
    autres_total     = tickets.exclude(module__in=['hotel','restaurant','bar','piscine']).aggregate(s=Sum('montant_total'))['s'] or 0

    return {
        'total': int(total),
        'nb_tickets': nb_tickets,
        'especes': int(especes),
        'mobile': int(mobile),
        'carte': int(carte),
        'virement': int(virement),
        'hotel': int(hotel_total),
        'restaurant': int(restaurant_total),
        'bar': int(bar_total),
        'piscine': int(piscine_total),
        'autres': int(autres_total),
        'tickets': tickets.select_related('client', 'cree_par').order_by('-date_creation')[:50],
    }


@require_module_access('caisse')
def index(request):
    today = timezone.now().date()
    is_manager = request.user.groups.filter(name=GROUPE_MANAGER_GENERAL).exists() or request.user.is_superuser

    # Ouvrir/Fermer caisse
    if request.method == 'POST':
        action = request.POST.get('action')
        session = CaisseSession.objects.filter(user=request.user, is_open=True).first()
        if action == 'ouvrir':
            if not session:
                CaisseSession.objects.create(user=request.user)
                messages.success(request, "Caisse ouverte avec succès.")
            else:
                messages.warning(request, "Votre caisse est déjà ouverte.")
        elif action == 'fermer':
            if session:
                session.is_open = False
                session.closed_at = timezone.now()
                session.save()
                messages.success(request, f"Caisse fermée. Total encaissé : {get_stats_caisse(today, request.user)['total']:,} F")
            else:
                messages.warning(request, "Aucune caisse ouverte.")
        return redirect('caisse:index')

    session_active = CaisseSession.objects.filter(user=request.user, is_open=True).first()
    stats = get_stats_caisse(today, None if is_manager else request.user)

    # Sessions du jour
    sessions_jour = CaisseSession.objects.filter(
        opened_at__date=today
    ).select_related('user').order_by('-opened_at')

    # Historique sessions (7 derniers jours)
    from datetime import timedelta
    sessions_histo = CaisseSession.objects.filter(
        opened_at__date__gte=today - timedelta(days=7),
        is_open=False
    ).select_related('user').order_by('-opened_at')[:20]

    context = {
        'today': today,
        'session_active': session_active,
        'is_manager': is_manager,
        'stats': stats,
        'sessions_jour': sessions_jour,
        'sessions_histo': sessions_histo,
    }
    return render(request, 'caisse/index.html', context)


@require_manager
def suivi_caisse(request):
    """Suivi de caisse — réservé Manager Général."""
    from datetime import timedelta, date as dt
    from django.db.models import Sum
    from facturation.models import Ticket

    # Période : 30 derniers jours
    today = timezone.now().date()
    debut = today - timedelta(days=29)

    # Stats par jour
    from django.db.models.functions import TruncDate
    stats_jours = (
        Ticket.objects
        .filter(date_creation__date__range=[debut, today])
        .annotate(jour=TruncDate('date_creation'))
        .values('jour')
        .annotate(total=Sum('montant_total'), nb=Sum('id') * 0 + 1)
        .order_by('jour')
    )

    # Stats par module sur la période
    stats_modules = {}
    for mod in ['hotel','restaurant','bar','piscine']:
        t = Ticket.objects.filter(
            date_creation__date__range=[debut, today],
            module=mod
        ).aggregate(s=Sum('montant_total'))['s'] or 0
        stats_modules[mod] = int(t)

    # Stats par mode de paiement
    modes = ['especes','mobile_money','carte_bancaire','virement']
    stats_modes = {}
    for mode in modes:
        t = Ticket.objects.filter(
            date_creation__date__range=[debut, today],
            mode_paiement__in=[mode, 'orange_money', 'wave', 'moov_money', 'mtn_money'] if mode == 'mobile_money' else [mode]
        ).aggregate(s=Sum('montant_total'))['s'] or 0
        stats_modes[mode] = int(t)

    # Sessions caisse
    sessions = CaisseSession.objects.filter(
        opened_at__date__range=[debut, today]
    ).select_related('user').order_by('-opened_at')

    context = {
        'today': today,
        'debut': debut,
        'stats_jours': list(stats_jours),
        'stats_modules': stats_modules,
        'stats_modes': stats_modes,
        'sessions': sessions,
        'total_periode': sum(stats_modules.values()),
    }
    return render(request, 'caisse/suivi.html', context)
