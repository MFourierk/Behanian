from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from decimal import Decimal, InvalidOperation

from utils.permissions import require_module_access, require_manager, GROUPE_MANAGER_GENERAL
from facturation.models import Ticket
from .models import CaisseSession, MouvementCaisse, PrelevementBanque


# ── Modules à réconcilier (ticket_module, caisse_module, label, emoji) ─────
MODULES_RECONCILIATION = [
    ('hotel',      'hotel',    'Hôtel',        '🏨'),
    ('restaurant', 'restaurant','Restaurant',  '🍽️'),
    ('cave',       'cave',     'Cave / Bar',   '🍷'),
    ('piscine',    'piscine',  'Piscine',      '🏊'),
    ('espace',     'espaces',  'Espaces',      '🎪'),
]


def get_reconciliation_jour(date=None):
    """
    Retourne par module : total transactions du jour, total versé manuellement,
    solde restant à verser.
    """
    if date is None:
        date = timezone.localdate()

    lignes = []
    grand_total_tx = 0
    grand_total_verse = 0

    for ticket_mod, caisse_mod, label, emoji in MODULES_RECONCILIATION:
        total_tx = int(
            Ticket.objects.filter(date_creation__date=date, module=ticket_mod)
            .aggregate(s=Sum('montant_total'))['s'] or 0
        )
        total_verse = int(
            MouvementCaisse.objects.filter(
                date__date=date,
                type='versement',
                module=caisse_mod,
                valide=True,
            ).exclude(reference__startswith='CONSOLIDATION')
            .aggregate(s=Sum('montant'))['s'] or 0
        )
        solde = total_tx - total_verse
        lignes.append({
            'label':       label,
            'emoji':       emoji,
            'total_tx':    total_tx,
            'total_verse': total_verse,
            'solde':       solde,
            'complet':     solde <= 0,
        })
        grand_total_tx    += total_tx
        grand_total_verse += total_verse

    return {
        'lignes':             lignes,
        'grand_total_tx':     grand_total_tx,
        'grand_total_verse':  grand_total_verse,
        'grand_solde':        grand_total_tx - grand_total_verse,
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def _dec(val, default=0):
    try:
        return Decimal(str(val or default))
    except (InvalidOperation, TypeError):
        return Decimal(str(default))


def get_stats_jour(date=None, type_caisse=None):
    """Stats complètes d'une journée.
    - type_caisse=None ou 'centrale' : toutes les transactions
    - type_caisse='hotel'            : tickets hotel uniquement
    - type_caisse='module'           : tickets hors hotel
    """
    if date is None:
        date = timezone.now().date()

    tickets = Ticket.objects.filter(date_creation__date=date)

    if type_caisse == 'hotel':
        tickets = tickets.filter(module__in=['hotel'])
    elif type_caisse == 'module':
        tickets = tickets.exclude(module__in=['hotel'])

    total    = tickets.aggregate(s=Sum('montant_total'))['s'] or 0
    especes  = tickets.filter(mode_paiement='especes').aggregate(s=Sum('montant_total'))['s'] or 0
    mobile   = tickets.filter(mode_paiement__in=['mobile_money', 'orange_money', 'wave', 'moov_money', 'mtn_money']).aggregate(s=Sum('montant_total'))['s'] or 0
    carte    = tickets.filter(mode_paiement='carte_bancaire').aggregate(s=Sum('montant_total'))['s'] or 0
    virement = tickets.filter(mode_paiement='virement').aggregate(s=Sum('montant_total'))['s'] or 0

    par_module = {}
    for mod, label in [('hotel', 'Hôtel'), ('restaurant', 'Restaurant'), ('cave', 'Cave'),
                        ('piscine', 'Piscine'), ('espace', 'Espaces'), ('caisse', 'Caisse')]:
        t = tickets.filter(module__startswith=mod).aggregate(s=Sum('montant_total'))['s'] or 0
        if t:
            par_module[label] = int(t)

    prelevements   = PrelevementBanque.objects.filter(date__date=date, valide=True)
    total_prelev   = prelevements.aggregate(s=Sum('montant'))['s'] or 0
    depenses       = MouvementCaisse.objects.filter(date__date=date, type='depense', valide=True)
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
        'tickets': tickets.select_related('client', 'cree_par').order_by('-date_creation'),
    }


def get_solde_veille():
    """Retourne le solde restant après la dernière clôture de la caisse centrale."""
    last = CaisseSession.objects.filter(is_open=False, type_caisse='centrale').order_by('-closed_at').first()
    if not last:
        return 0, None
    solde = last.fond_caisse_reel + last.total_especes - last.prelevement_banque
    return int(solde), last


def _session_centrale_non_cloturee():
    """Retourne la session centrale ouverte d'un jour antérieur, ou None."""
    today = timezone.localdate()
    return CaisseSession.objects.filter(
        is_open=True,
        type_caisse='centrale',
        date_session__lt=today,
    ).order_by('-date_session').first()


# ── Vues principales ───────────────────────────────────────────────────────

@require_module_access('caisse')
def index(request):
    today = timezone.localdate()
    is_manager = request.user.groups.filter(name=GROUPE_MANAGER_GENERAL).exists() or request.user.is_superuser
    session_active = CaisseSession.objects.filter(user=request.user, is_open=True).first()

    user_type = None
    if session_active:
        user_type = session_active.type_caisse
    elif not is_manager:
        user_groups = list(request.user.groups.values_list('name', flat=True))
        if 'Réceptionniste' in user_groups or 'Responsable Hôtel' in user_groups:
            user_type = 'hotel'
        elif not any(g in user_groups for g in ['Manager Général(e)', 'Directeur Général', 'Chef caissier(e)']):
            user_type = 'module'

    stats = get_stats_jour(today, type_caisse=user_type)

    sessions_jour = CaisseSession.objects.filter(
        opened_at__date=today
    ).select_related('user').order_by('-opened_at')

    mouvements = MouvementCaisse.objects.filter(
        date__date=today, valide=True
    ).select_related('cree_par').order_by('-date')

    prelevements = PrelevementBanque.objects.filter(
        date__date=today, valide=True
    ).select_related('cree_par').order_by('-date')

    solde_veille, last_session = get_solde_veille()

    # Sessions centrales non clôturées des jours précédents (alerte manager)
    sessions_bloquantes = CaisseSession.objects.filter(
        is_open=True,
        type_caisse='centrale',
        date_session__lt=today,
    ).select_related('user').order_by('-date_session')

    can_open_caisse = (
        request.user.is_superuser or
        any(g in list(request.user.groups.values_list('name', flat=True)) for g in [
            'Chef caissier(e)', 'Caissier(ère) Principal(e)', 'Caissier(ere) Principal(e)',
            'Manager Général(e)', 'Manager General(e)',
            'Réceptionniste', 'Receptionniste', 'Responsable Hôtel',
            'Caissière / Caissier', 'Caissiere / Caissier',
        ])
    )

    reconciliation = get_reconciliation_jour(today)

    context = {
        'billetage_vals': [10000, 5000, 2000, 1000, 500, 250, 200, 100, 50, 25],
        'today': today,
        'session_active': session_active,
        'is_manager': is_manager,
        'can_open_caisse': can_open_caisse,
        'stats': stats,
        'sessions_jour': sessions_jour,
        'mouvements': mouvements,
        'prelevements': prelevements,
        'solde_veille': solde_veille,
        'last_session': last_session,
        'sessions_bloquantes': sessions_bloquantes,
        'reconciliation': reconciliation,
    }
    return render(request, 'caisse/index.html', context)


# Groupes autorisés à ouvrir la caisse centrale
GROUPES_CAISSE_CENTRALE = [
    'Chef caissier(e)',
    'Caissier(ère) Principal(e)',
    'Caissier(ere) Principal(e)',
    'Manager Général(e)',
    'Manager General(e)',
]


def _get_type_caisse(user):
    """Seule la caisse centrale est ouverte/clôturée. Tous les utilisateurs autorisés ouvrent la centrale."""
    return 'centrale'


@require_module_access('caisse')
@require_POST
def ouvrir_caisse(request):
    today = timezone.localdate()
    type_attendu = _get_type_caisse(request.user)

    # 1. Vérifier si une session est déjà ouverte pour cet utilisateur aujourd'hui
    session_existante = CaisseSession.objects.filter(
        user=request.user, is_open=True, type_caisse=type_attendu
    ).first()
    if session_existante:
        return JsonResponse({
            'success': False,
            'error': f'Votre caisse {session_existante.get_type_caisse_display()} est déjà ouverte (depuis {session_existante.opened_at.strftime("%H:%M")})',
        })

    # 2. Bloquer si la caisse centrale du jour précédent n'a pas été clôturée
    session_ancienne = _session_centrale_non_cloturee()
    if session_ancienne:
        return JsonResponse({
            'success': False,
            'error': (
                f'⛔ Ouverture impossible : la caisse centrale du {session_ancienne.date_session.strftime("%d/%m/%Y")} '
                f'n\'a pas été clôturée. La clôture de fin de journée est obligatoire pour '
                f'positionner le solde de veille. Veuillez clôturer cette session avant d\'ouvrir une nouvelle journée.'
            ),
            'session_bloquante_id': session_ancienne.pk,
            'bloquee': True,
        })

    try:
        data  = json.loads(request.body)
        fond  = _dec(data.get('fond_caisse', 0))
        notes = data.get('notes', '')

        session = CaisseSession.objects.create(
            user=request.user,
            type_caisse=type_attendu,
            date_session=today,
            fond_caisse=fond,
            notes=notes,
        )

        # Fond de caisse comme premier mouvement
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

        # ── Consolidation automatique pour la caisse centrale ──────────────
        msg_consolidation = ''
        if type_attendu == 'centrale':
            sessions_autres = CaisseSession.objects.filter(
                opened_at__date=today,
                type_caisse__in=['hotel', 'module']
            ).exclude(id=session.id)

            total_consolide = _dec(0)
            nb_sessions = sessions_autres.count()

            for s in sessions_autres:
                stats_s  = get_stats_jour(today, type_caisse=s.type_caisse)
                montant_s = _dec(stats_s['total'])
                if montant_s > 0:
                    total_consolide += montant_s
                    MouvementCaisse.objects.get_or_create(
                        session=session,
                        type='versement',
                        module='caisse',
                        reference=f'CONSOLIDATION-{s.pk}',
                        defaults={
                            'montant': montant_s,
                            'mode_paiement': 'especes',
                            'description': f'Consolidation auto — {s.get_type_caisse_display()} ({s.user.get_full_name() or s.user.username})',
                            'cree_par': request.user,
                        }
                    )

            if nb_sessions > 0:
                msg_consolidation = f' | {nb_sessions} caisse(s) consolidée(s) : {int(total_consolide):,} F'
        # ──────────────────────────────────────────────────────────────────

        return JsonResponse({
            'success': True,
            'message': f'Caisse ouverte — {session.numero_session} — Fond: {int(fond):,} F{msg_consolidation}',
            'opened_at': session.opened_at.strftime("%d/%m/%Y à %H:%M"),
            'numero_session': session.numero_session,
            'type_caisse': type_attendu,
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
        data      = json.loads(request.body)
        today     = timezone.localdate()
        fond_reel = _dec(data.get('fond_reel', 0))
        prelev    = _dec(data.get('prelevement_banque', 0))
        banque    = data.get('banque', '')
        notes     = data.get('notes', '')

        stats = get_stats_jour(today, type_caisse=session.type_caisse)

        # Solde théorique = fond initial + espèces encaissées − prélèvements banque
        solde_th = session.fond_caisse + _dec(stats['especes']) - prelev
        ecart    = solde_th - fond_reel

        session.closed_at          = timezone.now()
        session.is_open            = False
        session.fond_caisse_reel   = fond_reel
        session.total_especes      = stats['especes']
        session.total_mobile       = stats['mobile']
        session.total_carte        = stats['carte']
        session.total_virement     = stats['virement']
        session.total_general      = stats['total']
        session.prelevement_banque = prelev
        session.solde_theorique    = solde_th
        session.ecart              = ecart
        session.notes              = notes
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

        ecart_label = f"+{int(ecart):,} F (excédent)" if ecart > 0 else (f"{int(ecart):,} F (manquant)" if ecart < 0 else "0 F (équilibré)")
        return JsonResponse({
            'success': True,
            'message': f'Caisse clôturée — {session.numero_session}. Total: {stats["total"]:,} F | Écart: {ecart_label}',
            'total': stats['total'],
            'prelev': int(prelev),
            'solde_theorique': int(solde_th),
            'ecart': int(ecart),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_manager
@require_POST
def force_cloturer_caisse(request, session_id):
    """Clôture forcée d'une session bloquante par un manager."""
    session = get_object_or_404(CaisseSession, pk=session_id, is_open=True)
    try:
        data      = json.loads(request.body) if request.body else {}
        fond_reel = _dec(data.get('fond_reel', session.fond_caisse))
        notes     = data.get('notes', 'Clôture forcée par manager')

        date = session.date_session
        stats = get_stats_jour(date, type_caisse=session.type_caisse)

        solde_th = session.fond_caisse + _dec(stats['especes']) - session.prelevement_banque
        ecart    = solde_th - fond_reel

        session.closed_at        = timezone.now()
        session.is_open          = False
        session.fond_caisse_reel = fond_reel
        session.total_especes    = stats['especes']
        session.total_mobile     = stats['mobile']
        session.total_carte      = stats['carte']
        session.total_virement   = stats['virement']
        session.total_general    = stats['total']
        session.solde_theorique  = solde_th
        session.ecart            = ecart
        session.notes            = notes + f' — forcée par {request.user.get_full_name() or request.user.username}'
        session.save()

        return JsonResponse({
            'success': True,
            'message': f'Session {session.numero_session} du {session.date_session.strftime("%d/%m/%Y")} clôturée de force.',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
@require_POST
def enregistrer_mouvement(request):
    """Dépense, remboursement, ajustement manuel."""
    try:
        data    = json.loads(request.body)
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
        data    = json.loads(request.body)
        montant = _dec(data.get('montant', 0))
        if montant <= 0:
            return JsonResponse({'success': False, 'error': 'Montant invalide'})
        session = CaisseSession.objects.filter(user=request.user, is_open=True).first()

        PrelevementBanque.objects.create(
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
            description=f'Prélèvement banque — {data.get("banque", "")}',
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
        today = timezone.localdate()
        session = CaisseSession.objects.filter(
            opened_at__date=today, user=request.user
        ).order_by('-opened_at').first()

    if not session:
        return redirect('caisse:index')

    date         = session.date_session or session.opened_at.date()
    stats        = get_stats_jour(date)
    mouvements   = MouvementCaisse.objects.filter(session=session, valide=True).order_by('date')
    prelevements = PrelevementBanque.objects.filter(session=session, valide=True).order_by('date')

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
    stats.pop('tickets', None)
    return JsonResponse(stats)


@require_module_access('caisse')
@require_POST
def sync_centrale(request):
    """Re-synchronise en temps réel les caisses modules/hotel dans la session centrale."""
    session = CaisseSession.objects.filter(
        user=request.user, is_open=True, type_caisse='centrale'
    ).first()
    if not session:
        return JsonResponse({'success': False, 'error': 'Aucune session centrale ouverte pour cet utilisateur'})

    try:
        today          = timezone.localdate()
        sessions_autres = CaisseSession.objects.filter(
            opened_at__date=today,
            type_caisse__in=['hotel', 'module']
        ).exclude(id=session.id)

        total_consolide = _dec(0)
        nb_updates      = 0

        for s in sessions_autres:
            stats_s   = get_stats_jour(today, type_caisse=s.type_caisse)
            montant_s = _dec(stats_s['total'])
            ref       = f'CONSOLIDATION-{s.pk}'

            existing = MouvementCaisse.objects.filter(session=session, reference=ref).first()
            if existing:
                if montant_s > 0 and existing.montant != montant_s:
                    existing.montant     = montant_s
                    existing.description = (
                        f'Consolidation sync — {s.get_type_caisse_display()} '
                        f'({s.user.get_full_name() or s.user.username})'
                    )
                    existing.save()
                    nb_updates += 1
            elif montant_s > 0:
                MouvementCaisse.objects.create(
                    session=session,
                    type='versement',
                    module='caisse',
                    reference=ref,
                    montant=montant_s,
                    mode_paiement='especes',
                    description=(
                        f'Consolidation — {s.get_type_caisse_display()} '
                        f'({s.user.get_full_name() or s.user.username})'
                    ),
                    cree_par=request.user,
                )
                nb_updates += 1

            total_consolide += montant_s

        return JsonResponse({
            'success': True,
            'message': f'Synchronisation OK — {int(total_consolide):,} F | {nb_updates} mise(s) à jour',
            'total': int(total_consolide),
            'nb_sessions': sessions_autres.count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_module_access('caisse')
def api_reconciliation(request):
    """API JSON — état des transactions vs versements par module pour le jour."""
    today = timezone.localdate()
    data = get_reconciliation_jour(today)
    return JsonResponse({'success': True, 'reconciliation': data})


@require_manager
def historique(request):
    """Historique complet des sessions — Manager."""
    from datetime import timedelta
    today = timezone.localdate()
    debut = today - timedelta(days=30)

    sessions = CaisseSession.objects.filter(
        opened_at__date__gte=debut
    ).select_related('user').order_by('-opened_at')

    return render(request, 'caisse/historique.html', {
        'sessions': sessions,
        'today': today,
        'debut': debut,
    })
