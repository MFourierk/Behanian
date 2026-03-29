from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal, InvalidOperation

from utils.permissions import require_module_access, require_manager, GROUPE_MANAGER_GENERAL
from facturation.models import Ticket
from .models import CaisseSession, MouvementCaisse, PrelevementBanque


# ── Helpers ────────────────────────────────────────────────────────────────

def _dec(val, default=0):
    try:
        return Decimal(str(val or default))
    except (InvalidOperation, TypeError):
        return Decimal(str(default))


def get_stats_jour(date=None):
    """Stats complètes d'une journée depuis les tickets + mouvements caisse."""
    if date is None:
        date = timezone.now().date()

    tickets = Ticket.objects.filter(date_creation__date=date)

    total         = tickets.aggregate(s=Sum('montant_total'))['s'] or 0
    especes       = tickets.filter(mode_paiement='especes').aggregate(s=Sum('montant_total'))['s'] or 0
    mobile        = tickets.filter(mode_paiement__in=['mobile_money','orange_money','wave','moov_money','mtn_money']).aggregate(s=Sum('montant_total'))['s'] or 0
    carte         = tickets.filter(mode_paiement='carte_bancaire').aggregate(s=Sum('montant_total'))['s'] or 0
    virement      = tickets.filter(mode_paiement='virement').aggregate(s=Sum('montant_total'))['s'] or 0

    # Par module
    par_module = {}
    for mod, label in [('hotel','Hôtel'),('restaurant','Restaurant'),('cave','Cave'),('piscine','Piscine'),('espace','Espaces'),('caisse','Caisse')]:
        t = tickets.filter(module__startswith=mod).aggregate(s=Sum('montant_total'))['s'] or 0
        if t: par_module[label] = int(t)

    # Prélèvements banque du jour
    prelevements = PrelevementBanque.objects.filter(date__date=date, valide=True)
    total_prelev  = prelevements.aggregate(s=Sum('montant'))['s'] or 0

    # Dépenses du jour
    depenses = MouvementCaisse.objects.filter(date__date=date, type='depense', valide=True)
    total_depenses = depenses.aggregate(s=Sum('montant'))['s'] or 0

    return {
        'date': date,
        'total': int(total),
        'nb_tickets': tickets.count(),
        'especes': int(especes),
        'mobile': int(mobile),
        'carte': int(carte),
        'virement': int(virement),
        'par_module': par_module,
        'prelevements': int(total_prelev),
        'depenses': int(total_depenses),
        'net': int(total) - int(total_prelev) - int(total_depenses),
        'tickets': tickets.select_related('client','cree_par').order_by('-date_creation'),
    }


# ── Vues principales ───────────────────────────────────────────────────────

def get_solde_veille():
    """Retourne le solde restant après la dernière clôture."""
    last = CaisseSession.objects.filter(is_open=False).order_by('-closed_at').first()
    if not last:
        return 0, None
    # Solde = fond réel compté + espèces encaissées - prélèvement banque
    solde = last.fond_caisse_reel + last.total_especes - last.prelevement_banque
    return int(solde), last


@require_module_access('caisse')
def index(request):
    today = timezone.now().date()
    is_manager = request.user.groups.filter(name=GROUPE_MANAGER_GENERAL).exists() or request.user.is_superuser
    session_active = CaisseSession.objects.filter(user=request.user, is_open=True).first()
    stats = get_stats_jour(today)

    # Sessions du jour (toutes)
    sessions_jour = CaisseSession.objects.filter(
        opened_at__date=today
    ).select_related('user').order_by('-opened_at')

    # Mouvements du jour
    mouvements = MouvementCaisse.objects.filter(
        date__date=today, valide=True
    ).select_related('cree_par').order_by('-date')

    # Prélèvements du jour
    prelevements = PrelevementBanque.objects.filter(
        date__date=today, valide=True
    ).select_related('cree_par').order_by('-date')

    solde_veille, last_session = get_solde_veille()
    context = {
        'today': today,
        'session_active': session_active,
        'is_manager': is_manager,
        'stats': stats,
        'sessions_jour': sessions_jour,
        'mouvements': mouvements,
        'prelevements': prelevements,
        'solde_veille': solde_veille,
        'last_session': last_session,
    }
    return render(request, 'caisse/index.html', context)


@require_module_access('caisse')
@require_POST
def ouvrir_caisse(request):
    session = CaisseSession.objects.filter(user=request.user, is_open=True).first()
    if session:
        return JsonResponse({'success': False, 'error': 'Caisse déjà ouverte'})
    try:
        data = json.loads(request.body)
        fond = _dec(data.get('fond_caisse', 0))
        notes = data.get('notes', '')
        # Déterminer le type de caisse selon le groupe de l'utilisateur
        user_groups = list(request.user.groups.values_list('name', flat=True))
        if request.user.is_superuser or any(g in user_groups for g in ['Manager Général(e)', 'Directeur Général', 'Responsable Caisse']):
            type_caisse = 'centrale'
        elif 'Réceptionniste' in user_groups or 'Responsable Hôtel' in user_groups:
            type_caisse = 'hotel'
        else:
            type_caisse = 'module'  # Caissier(e) → Restaurant, Cave, Piscine, Espaces

        session = CaisseSession.objects.create(
            user=request.user,
            type_caisse=type_caisse,
            fond_caisse=fond,
            notes=notes,
        )
        # Enregistrer le fond comme premier mouvement
        if fond > 0:
            MouvementCaisse.objects.create(
                session=session,
                type='fond_caisse',
                module='caisse',
                montant=fond,
                mode_paiement='especes',
                description=f'Fond de caisse — ouverture {session.opened_at.strftime("%d/%m/%Y %H:%M")}',
                cree_par=request.user,
            )
        return JsonResponse({
            'success': True,
            'message': f'Caisse ouverte — Fond: {int(fond):,} F',
            'opened_at': session.opened_at.strftime('%d/%m/%Y à %H:%M'),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
@require_POST
def cloturer_caisse(request):
    session = CaisseSession.objects.filter(user=request.user, is_open=True).first()
    if not session:
        return JsonResponse({'success': False, 'error': 'Aucune caisse ouverte'})
    try:
        data = json.loads(request.body)
        today = timezone.now().date()
        stats = get_stats_jour(today)

        fond_reel = _dec(data.get('fond_reel', 0))
        prelev    = _dec(data.get('prelevement_banque', 0))
        banque    = data.get('banque', '')
        notes     = data.get('notes', '')

        # Clôturer la session
        session.closed_at        = timezone.now()
        session.is_open          = False
        session.fond_caisse_reel = fond_reel
        session.total_especes    = stats['especes']
        session.total_mobile     = stats['mobile']
        session.total_carte      = stats['carte']
        session.total_virement   = stats['virement']
        session.total_general    = stats['total']
        session.prelevement_banque = prelev
        session.notes            = notes
        session.save()

        # Enregistrer le prélèvement banque si > 0
        if prelev > 0:
            PrelevementBanque.objects.create(
                session=session,
                montant=prelev,
                banque=banque,
                notes=notes,
                cree_par=request.user,
            )
            MouvementCaisse.objects.create(
                session=session,
                type='prelevement',
                module='banque',
                montant=prelev,
                mode_paiement='virement',
                description=f'Prélèvement banque à la clôture — {banque}',
                cree_par=request.user,
            )

        return JsonResponse({
            'success': True,
            'message': f'Caisse clôturée. Total: {stats["total"]:,} F',
            'total': stats['total'],
            'prelev': int(prelev),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
@require_POST
def enregistrer_mouvement(request):
    """Dépense, remboursement, ajustement manuel."""
    try:
        data = json.loads(request.body)
        session = CaisseSession.objects.filter(user=request.user, is_open=True).first()

        type_mv = data.get('type', 'depense')
        montant = _dec(data.get('montant', 0))
        if montant <= 0:
            return JsonResponse({'success': False, 'error': 'Montant invalide'})

        MouvementCaisse.objects.create(
            session=session,
            type=type_mv,
            module=data.get('module', 'caisse'),
            montant=montant,
            mode_paiement=data.get('mode_paiement', 'especes'),
            description=data.get('description', ''),
            reference=data.get('reference', ''),
            cree_par=request.user,
        )
        return JsonResponse({'success': True, 'message': f'Mouvement enregistré : {int(montant):,} F'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
@require_POST
def prelevement_banque(request):
    """Prélèvement vers la banque en cours de journée."""
    try:
        data = json.loads(request.body)
        montant = _dec(data.get('montant', 0))
        if montant <= 0:
            return JsonResponse({'success': False, 'error': 'Montant invalide'})
        session = CaisseSession.objects.filter(user=request.user, is_open=True).first()

        p = PrelevementBanque.objects.create(
            session=session,
            montant=montant,
            banque=data.get('banque', ''),
            reference=data.get('reference', ''),
            notes=data.get('notes', ''),
            cree_par=request.user,
        )
        MouvementCaisse.objects.create(
            session=session,
            type='prelevement',
            module='banque',
            montant=montant,
            mode_paiement='virement',
            description=f'Prélèvement banque — {data.get("banque","")}',
            reference=data.get('reference', ''),
            cree_par=request.user,
        )
        return JsonResponse({
            'success': True,
            'message': f'Prélèvement de {int(montant):,} F enregistré',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
def rapport_caisse(request, session_id=None):
    """Rapport imprimable d'une session de caisse."""
    if session_id:
        session = get_object_or_404(CaisseSession, pk=session_id)
    else:
        today = timezone.now().date()
        session = CaisseSession.objects.filter(
            opened_at__date=today, user=request.user
        ).order_by('-opened_at').first()

    if not session:
        return redirect('caisse:index')

    date = session.opened_at.date()
    stats = get_stats_jour(date)
    mouvements = MouvementCaisse.objects.filter(
        session=session, valide=True
    ).order_by('date')
    prelevements = PrelevementBanque.objects.filter(
        session=session, valide=True
    ).order_by('date')

    return render(request, 'caisse/rapport.html', {
        'session': session,
        'stats': stats,
        'mouvements': mouvements,
        'prelevements': prelevements,
    })


@require_module_access('caisse')
def api_stats_jour(request):
    """API stats pour une date donnée."""
    from datetime import date as dt
    date_str = request.GET.get('date')
    try:
        date = dt.fromisoformat(date_str) if date_str else timezone.now().date()
    except ValueError:
        date = timezone.now().date()
    stats = get_stats_jour(date)
    stats.pop('tickets', None)  # pas sérialisable
    return JsonResponse(stats)


@require_manager
def historique(request):
    """Historique complet des sessions — Manager."""
    from datetime import timedelta
    today = timezone.now().date()
    debut = today - timedelta(days=30)

    sessions = CaisseSession.objects.filter(
        opened_at__date__gte=debut
    ).select_related('user').order_by('-opened_at')

    stats_periode = get_stats_jour.__wrapped__(debut) if hasattr(get_stats_jour, '__wrapped__') else {}

    return render(request, 'caisse/historique.html', {
        'sessions': sessions,
        'today': today,
        'debut': debut,
    })
