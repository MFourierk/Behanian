from utils.permissions import require_module_access, require_superuser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from .models import Facture, Proforma, Avoir, Client, Service, Article, LigneFacture, LigneProforma, LigneAvoir, Ticket
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import json
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q
from hotel.models import Chambre
from restaurant.models import PlatMenu
from espaces_evenementiels.models import EspaceEvenementiel

from django.conf import settings
import os

# Constantes pour les informations de l'entreprise
NOM_ENTREPRISE = "Complexe Hôtelier BEHANIAN"
ADRESSE_ENTREPRISE = "Yopougon Beago à 2000m du Palais de justice"
TELEPHONE_ENTREPRISE = "07 58 29 11 10 / 01 43 09 76 16"
EMAIL_ENTREPRISE = "complexebehanian@gmail.com"

def get_logo_path():
    """
    Récupère le chemin absolu du logo pour WeasyPrint.
    Gère intelligemment le développement (BASE_DIR) et la production (STATIC_ROOT).
    """
    # Nom du fichier logo
    filename = 'Logo.png'
    
    # 1. Tentative via STATIC_ROOT (Configuration de Production)
    if not settings.DEBUG and hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        prod_path = os.path.join(settings.STATIC_ROOT, 'images', filename)
        if os.path.exists(prod_path):
            return prod_path

    # 2. Fallback Développement : Chemin direct dans le dossier static du projet
    dev_path = os.path.join(settings.BASE_DIR, 'static', 'images', filename)
    return dev_path

@require_module_access('facturation')
def index(request):
    """Vue principale du module facturation"""
    from django.utils import timezone
    from django.db.models import Sum, Count, Q
    today = timezone.now().date()

    # KPIs tickets
    tickets_jour = Ticket.objects.filter(date_creation__date=today)
    ca_jour = tickets_jour.aggregate(s=Sum('montant_total'))['s'] or 0
    tickets_mois = Ticket.objects.filter(
        date_creation__month=today.month, date_creation__year=today.year
    )
    ca_mois = tickets_mois.aggregate(s=Sum('montant_total'))['s'] or 0

    # KPIs documents
    factures_impayees = Facture.objects.filter(statut__in=['envoyee', 'en_attente', 'impayee'])
    montant_impaye = factures_impayees.aggregate(s=Sum('total'))['s'] or 0

    # Tickets récents tous modules
    tickets_recents = Ticket.objects.select_related('client','cree_par').order_by('-date_creation')[:50]

    # Répartition CA par module
    ca_par_module = {}
    for m, l in [('hotel','Hôtel'),('restaurant','Restaurant'),('cave','Cave'),('piscine','Piscine'),('caisse','Caisse'),('autre','Autre')]:
        ca = Ticket.objects.filter(module=m).aggregate(s=Sum('montant_total'))['s'] or 0
        if ca > 0:
            ca_par_module[l] = int(ca)

    # Documents récents
    recent_factures = Facture.objects.select_related('client').order_by('-date_creation')[:8]
    recent_proformas = Proforma.objects.select_related('client').order_by('-date_creation')[:8]
    recent_avoirs = Avoir.objects.select_related('client').order_by('-date_creation')[:8]

    # Services et JSON
    services = Service.objects.all()
    services_json = json.dumps([{'id': s.id, 'nom': s.nom} for s in services])

    # Clients pour formulaires
    clients = Client.objects.all().order_by('nom')

    context = {
        # KPIs
        'ca_jour': int(ca_jour),
        'ca_mois': int(ca_mois),
        'nb_tickets_jour': tickets_jour.count(),
        'nb_tickets_mois': tickets_mois.count(),
        'nb_factures_impayees': factures_impayees.count(),
        'montant_impaye': int(montant_impaye),
        'nb_proformas': Proforma.objects.filter(statut='en_attente').count(),
        'nb_avoirs': Avoir.objects.filter(statut='en_attente').count(),
        # Données
        'tickets_recents': tickets_recents,
        'ca_par_module': ca_par_module,
        'recent_factures': recent_factures,
        'recent_proformas': recent_proformas,
        'recent_avoirs': recent_avoirs,
        'total_tickets': Ticket.objects.count(),
        'total_factures': Facture.objects.count(),
        'total_proformas': Proforma.objects.count(),
        'total_avoirs': Avoir.objects.count(),
        # Forms
        'services': services,
        'services_json': services_json,
        'clients': clients,
    }
    return render(request, 'facturation/index.html', context)

@require_module_access('facturation')
def facture_list(request):
    date_debut_str = request.GET.get('date_debut', '')
    date_fin_str   = request.GET.get('date_fin', '')
    date_debut = date_fin = None
    try:
        if date_debut_str:
            date_debut = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        if date_fin_str:
            date_fin = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    factures = Facture.objects.select_related('client', 'cree_par').order_by('-date_creation')
    if date_debut:
        factures = factures.filter(date_facturation__gte=date_debut)
    if date_fin:
        factures = factures.filter(date_facturation__lte=date_fin)

    total_ttc  = factures.aggregate(s=Sum('total'))['s'] or Decimal('0')
    total_paye = factures.aggregate(s=Sum('montant_paye'))['s'] or Decimal('0')
    stats = {
        'nb':       factures.count(),
        'total_ttc': total_ttc,
        'total_paye': total_paye,
        'reste_du': total_ttc - total_paye,
    }
    return render(request, 'facturation/facture_list.html', {
        'factures':   factures,
        'stats':      stats,
        'date_debut': date_debut_str,
        'date_fin':   date_fin_str,
    })

@require_module_access('facturation')
def facture_create(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Gérer le client
                client_name = request.POST.get('client_name')
                client_phone = request.POST.get('client_phone')
                client_email = request.POST.get('client_email')
                client_address = request.POST.get('client_address')

                client, created = Client.objects.get_or_create(
                    nom=client_name,
                    defaults={
                        'telephone': client_phone,
                        'email': client_email,
                        'adresse': client_address or ''
                    }
                )

                # 2. Créer l'objet Facture principal
                date_creation_str = request.POST.get('date_creation')
                if date_creation_str:
                    date_creation = timezone.datetime.strptime(date_creation_str, '%Y-%m-%d')
                    if timezone.is_naive(date_creation):
                        date_creation = timezone.make_aware(date_creation)
                else:
                    date_creation = timezone.now()

                facture = Facture.objects.create(
                    client=client,
                    cree_par=request.user,
                    remise=Decimal(request.POST.get('remise', 0)),
                    taux_tva=Decimal(request.POST.get('tva', 0)),
                    date_creation=date_creation,
                    date_facturation=date_creation.date()
                )

                # 3. Traiter les lignes d'articles
                i = 1
                while f'articles-{i}-service' in request.POST:
                    service_id = request.POST.get(f'articles-{i}-service')
                    composite_id = request.POST.get(f'articles-{i}-description')
                    quantity = request.POST.get(f'articles-{i}-quantity')
                    price = request.POST.get(f'articles-{i}-price')

                    if service_id and composite_id and quantity and price:
                        try:
                            content_type_id, object_id = composite_id.split(':')
                            service = get_object_or_404(Service, id=service_id)

                            article_wrapper, created = Article.objects.get_or_create(
                                content_type_id=content_type_id,
                                object_id=object_id,
                                defaults={'service': service}
                            )

                            LigneFacture.objects.create(
                                facture=facture,
                                article=article_wrapper,
                                quantite=Decimal(quantity),
                                prix_unitaire=Decimal(price)
                            )
                        except (ValueError, Service.DoesNotExist, ContentType.DoesNotExist) as e:
                            print(f"Skipping invalid article line: {i}. Error: {e}")
                    
                    i += 1

                # 4. Calculer les totaux
                facture.calculate_totals()

                pdf_url = reverse('facturation:facture_pdf', kwargs={'pk': facture.pk})
                facture_data = {
                    'id': facture.id,
                    'numero': facture.numero,
                    'client_nom': facture.client.nom,
                    'total_ttc': facture.total,
                    'date_creation': facture.date_creation.strftime('%d/%m/%Y'),
                    'pdf_url': pdf_url,
                    'detail_url': reverse('facturation:facture_detail', kwargs={'pk': facture.pk})
                }
                return JsonResponse({'success': True, 'facture': facture_data})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@require_module_access('facturation')
def facture_detail(request, pk):
    from types import SimpleNamespace
    facture = get_object_or_404(Facture, pk=pk)
    # Protéger client None
    if not facture.client:
        facture.client = SimpleNamespace(nom='Client anonyme', telephone='', email='', adresse='')
    lignes = facture.lignes.order_by('id')
    return render(request, 'facturation/facture_detail.html', {'facture': facture, 'lignes': lignes})

@require_module_access('facturation')
def facture_pdf(request, pk):
    """Affiche la facture en mode impression (style bon de réception)."""
    import re
    facture = get_object_or_404(Facture, pk=pk)
    if not facture.client:
        from types import SimpleNamespace
        facture.client = SimpleNamespace(nom='Client anonyme', telephone=None, email=None, adresse=None)
    lignes = facture.lignes.order_by('id')

    # Récupérer infos depuis le ticket d'origine (via notes)
    module_ticket = ''
    serveur_ticket = ''
    if facture.notes:
        match = re.search(r'ticket\s+(TC-\S+)', facture.notes, re.IGNORECASE)
        if match:
            try:
                ticket = Ticket.objects.get(numero=match.group(1))
                module_ticket = ticket.get_module_display()
                # Serveur depuis data-serveur dans contenu
                if ticket.contenu:
                    srv_match = re.search(r'data-serveur="([^"]*)"', ticket.contenu)
                    if srv_match:
                        serveur_ticket = srv_match.group(1)
                # Fallback via commande restaurant
                if not serveur_ticket and ticket.module == 'restaurant' and ticket.objet_id:
                    try:
                        from restaurant.models import Commande
                        cmd = Commande.objects.select_related('serveur').filter(id=ticket.objet_id).first()
                        if cmd and cmd.serveur:
                            serveur_ticket = cmd.serveur.get_full_name() or cmd.serveur.username
                    except Exception:
                        pass
            except Ticket.DoesNotExist:
                pass

    return render(request, 'facturation/facture_pdf.html', {
        'facture': facture,
        'lignes': lignes,
        'module_ticket': module_ticket,
        'serveur_ticket': serveur_ticket,
    })

@require_module_access('facturation')
def proforma_list(request):
    date_debut_str = request.GET.get('date_debut', '')
    date_fin_str   = request.GET.get('date_fin', '')
    date_debut = date_fin = None
    try:
        if date_debut_str:
            date_debut = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        if date_fin_str:
            date_fin = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    proformas = Proforma.objects.select_related('client', 'cree_par').order_by('-date_creation')
    if date_debut:
        proformas = proformas.filter(date_creation__date__gte=date_debut)
    if date_fin:
        proformas = proformas.filter(date_creation__date__lte=date_fin)

    stats = {
        'nb':           proformas.count(),
        'total_ttc':    proformas.aggregate(s=Sum('total'))['s'] or Decimal('0'),
        'nb_convertis': proformas.filter(statut='convertie').count(),
    }
    return render(request, 'facturation/proforma_list.html', {
        'proformas':  proformas,
        'stats':      stats,
        'date_debut': date_debut_str,
        'date_fin':   date_fin_str,
    })

def _generer_numero_proforma():
    """Génère un numéro PRO-YYYY-XXXX automatique."""
    from django.utils import timezone as tz
    annee = tz.now().year
    last = Proforma.objects.filter(numero__startswith=f'PRO-{annee}-').order_by('numero').last()
    seq = int(last.numero.split('-')[-1]) + 1 if last else 1
    return f'PRO-{annee}-{seq:04d}'


@require_module_access('facturation')
def proforma_create(request):
    """Créer un proforma multi-services depuis le modal ou le formulaire POST JSON."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

    try:
        # Accepter JSON (modal index) ou POST form
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        client_name = data.get('client_name', '').strip()
        if not client_name:
            return JsonResponse({'success': False, 'error': 'Nom du client requis'})

        with transaction.atomic():
            # Client
            client, _ = Client.objects.get_or_create(
                nom=client_name,
                defaults={
                    'telephone': data.get('client_phone', ''),
                    'email': data.get('client_email', ''),
                    'adresse': data.get('client_address', ''),
                }
            )

            # Dates
            from datetime import date, timedelta
            from django.utils.dateparse import parse_date
            date_validite = parse_date(data.get('date_validite', '')) or (date.today() + timedelta(days=30))

            # Proforma
            proforma = Proforma.objects.create(
                numero=_generer_numero_proforma(),
                client=client,
                date_validite=date_validite,
                statut='en_attente',
                remise=Decimal(str(data.get('remise', '0') or '0')),
                taux_tva=Decimal(str(data.get('taux_tva', '0') or '0')),
                notes=data.get('notes', ''),
                cree_par=request.user,
            )

            # Lignes — format: [{service, designation, quantite, prix_unitaire}, ...]
            lignes_data = data.get('lignes', [])
            if isinstance(lignes_data, str):
                import json as _json
                lignes_data = _json.loads(lignes_data)

            sous_total = Decimal('0')
            for ld in lignes_data:
                designation = str(ld.get('designation', '')).strip()
                if not designation:
                    continue
                qte = Decimal(str(ld.get('quantite', '1') or '1'))
                prix = Decimal(str(ld.get('prix_unitaire', '0') or '0'))
                service_nom = str(ld.get('service', ''))

                LigneProforma.objects.create(
                    proforma=proforma,
                    article=None,
                    designation=designation,
                    description=service_nom,  # On stocke le service dans description
                    quantite=qte,
                    prix_unitaire=prix,
                )
                sous_total += qte * prix

            # Totaux
            net = sous_total - proforma.remise
            proforma.sous_total = sous_total
            proforma.montant_tva = net * (proforma.taux_tva / 100)
            proforma.total = net + proforma.montant_tva
            proforma.save()

            return JsonResponse({
                'success': True,
                'numero': proforma.numero,
                'detail_url': reverse('facturation:proforma_detail', kwargs={'pk': proforma.pk}),
                'pdf_url': reverse('facturation:proforma_pdf', kwargs={'pk': proforma.pk}),
            })

    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@require_module_access('facturation')
def proforma_detail(request, pk):
    proforma = get_object_or_404(Proforma, pk=pk)
    lignes = proforma.lignes.order_by('id')
    return render(request, 'facturation/proforma_detail.html', {'proforma': proforma, 'lignes': lignes})


@require_module_access('facturation')
def proforma_to_facture(request, pk):
    """Convertir un proforma en facture en un clic."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST requis'})
    proforma = get_object_or_404(Proforma, pk=pk)
    try:
        with transaction.atomic():
            annee = timezone.now().year
            last = Facture.objects.filter(numero__startswith=f'FAC-{annee}-').order_by('numero').last()
            seq = int(last.numero.split('-')[-1]) + 1 if last else 1
            numero = f'FAC-{annee}-{seq:04d}'

            from datetime import date, timedelta
            facture = Facture.objects.create(
                numero=numero,
                client=proforma.client,
                date_facturation=date.today(),
                date_echeance=date.today() + timedelta(days=30),
                statut='envoyee',
                sous_total=proforma.sous_total,
                remise=proforma.remise,
                taux_tva=proforma.taux_tva,
                montant_tva=proforma.montant_tva,
                total=proforma.total,
                montant_paye=0,
                notes=f'Converti depuis proforma {proforma.numero}',
                cree_par=request.user,
            )
            for lp in proforma.lignes.all():
                LigneFacture.objects.create(
                    facture=facture,
                    article=None,
                    designation=lp.designation,
                    description=lp.description,
                    quantite=lp.quantite,
                    prix_unitaire=lp.prix_unitaire,
                )
            proforma.statut = 'convertie'
            proforma.save()
            return JsonResponse({'success': True, 'detail_url': reverse('facturation:facture_detail', kwargs={'pk': facture.pk})})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_module_access('facturation')
def proforma_pdf(request, pk):
    """Affiche le proforma en mode impression."""
    proforma = get_object_or_404(Proforma, pk=pk)
    if not proforma.client:
        from types import SimpleNamespace
        proforma.client = SimpleNamespace(nom='Client anonyme', telephone=None, email=None, adresse=None)
    lignes = proforma.lignes.order_by('id')
    return render(request, 'facturation/proforma_pdf.html', {'proforma': proforma, 'lignes': lignes})

@require_module_access('facturation')
def avoir_list(request):
    date_debut_str = request.GET.get('date_debut', '')
    date_fin_str   = request.GET.get('date_fin', '')
    date_debut = date_fin = None
    try:
        if date_debut_str:
            date_debut = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        if date_fin_str:
            date_fin = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    avoirs = Avoir.objects.select_related('client', 'cree_par', 'facture_origine', 'ticket_origine').order_by('-date_creation')
    if date_debut:
        avoirs = avoirs.filter(date_avoir__gte=date_debut)
    if date_fin:
        avoirs = avoirs.filter(date_avoir__lte=date_fin)

    stats = {
        'nb':           avoirs.count(),
        'total_credits': avoirs.aggregate(s=Sum('total'))['s'] or Decimal('0'),
        'nb_traites':   avoirs.filter(statut='traitee').count(),
    }
    return render(request, 'facturation/avoir_list.html', {
        'avoirs':     avoirs,
        'stats':      stats,
        'date_debut': date_debut_str,
        'date_fin':   date_fin_str,
    })

def _generer_numero_avoir():
    annee = timezone.now().year
    last = Avoir.objects.filter(numero__startswith=f'AVO-{annee}-').order_by('numero').last()
    seq = int(last.numero.split('-')[-1]) + 1 if last else 1
    return f'AVO-{annee}-{seq:04d}'


@require_module_access('facturation')
def avoir_create(request):
    """Créer un avoir depuis le modal (JSON) ou depuis une facture/ticket."""
    if request.method != 'POST':
        # GET — afficher le formulaire avec pré-remplissage facture si ?facture=pk
        facture_id = request.GET.get('facture')
        facture = None
        if facture_id:
            try:
                facture = Facture.objects.select_related('client').get(pk=facture_id)
            except Facture.DoesNotExist:
                pass
        return render(request, 'facturation/avoir_form.html', {'facture': facture})

    try:
        # Accepter JSON (modal) ou POST form
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        client_name = data.get('client_name', '').strip()
        if not client_name:
            return JsonResponse({'success': False, 'error': 'Nom du client requis'})

        motif_select = data.get('motif_select', '')
        motif = data.get('motif', '') or motif_select
        if not motif:
            motif = 'Avoir'

        with transaction.atomic():
            client_obj, _ = Client.objects.get_or_create(
                nom=client_name,
                defaults={'telephone': data.get('client_phone', '')}
            )

            # Facture ou ticket d'origine
            facture_origine = None
            ticket_origine = None
            facture_id = data.get('facture_id') or data.get('facture')
            ticket_id = data.get('ticket_id')
            if facture_id:
                try:
                    facture_origine = Facture.objects.get(pk=facture_id)
                except Facture.DoesNotExist:
                    pass
            if ticket_id:
                try:
                    ticket_origine = Ticket.objects.get(pk=ticket_id)
                except Ticket.DoesNotExist:
                    pass

            montant = Decimal(str(data.get('montant', '0') or '0'))

            avoir = Avoir.objects.create(
                numero=_generer_numero_avoir(),
                client=client_obj,
                facture_origine=facture_origine,
                ticket_origine=ticket_origine,
                motif=motif,
                statut='en_attente',
                sous_total=montant,
                remise=0,
                taux_tva=0,
                montant_tva=0,
                total=montant,
                notes=data.get('notes', ''),
                cree_par=request.user,
                date_avoir=timezone.now().date(),
            )

            # Ligne unique avec le montant
            if montant > 0:
                LigneAvoir.objects.create(
                    avoir=avoir,
                    article=None,
                    designation=motif,
                    quantite=1,
                    prix_unitaire=montant,
                )

            # Si depuis modal index (JSON) → redirect vers détail
            if request.content_type and 'application/json' in request.content_type:
                return JsonResponse({
                    'success': True,
                    'numero': avoir.numero,
                    'detail_url': reverse('facturation:avoir_detail', kwargs={'pk': avoir.pk}),
                })

            return redirect('facturation:avoir_detail', pk=avoir.pk)

    except Exception as e:
        import traceback; traceback.print_exc()
        if request.content_type and 'application/json' in request.content_type:
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('facturation:avoir_list')

@require_module_access('facturation')
def avoir_detail(request, pk):
    avoir = get_object_or_404(Avoir, pk=pk)
    lignes = avoir.lignes.select_related('article__service').order_by('article__service__nom', 'id')
    return render(request, 'facturation/avoir_detail.html', {'avoir': avoir, 'lignes': lignes})

@require_module_access('facturation')
def avoir_pdf(request, pk):
    """Affiche l'avoir en mode impression."""
    avoir = get_object_or_404(Avoir, pk=pk)
    if not avoir.client:
        from types import SimpleNamespace
        avoir.client = SimpleNamespace(nom='Client anonyme', telephone=None, email=None, adresse=None)
    lignes = avoir.lignes.order_by('id')
    return render(request, 'facturation/avoir_pdf.html', {'avoir': avoir, 'lignes': lignes})


@require_module_access('facturation')
def ticket_list(request):
    today = timezone.now().date()

    # Date range filter : optionnel — vide = tout afficher
    date_debut_str = request.GET.get('date_debut', '')
    date_fin_str   = request.GET.get('date_fin', '')
    module_filter  = request.GET.get('module', '')
    query          = request.GET.get('q', '')

    date_debut = date_fin = None
    try:
        if date_debut_str:
            date_debut = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        if date_fin_str:
            date_fin = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    tickets = Ticket.objects.select_related('client', 'cree_par').order_by('-date_creation')

    if date_debut:
        tickets = tickets.filter(date_creation__date__gte=date_debut)
    if date_fin:
        tickets = tickets.filter(date_creation__date__lte=date_fin)
    if module_filter:
        tickets = tickets.filter(module=module_filter)
    if query:
        tickets = tickets.filter(
            Q(numero__icontains=query) | Q(client__nom__icontains=query)
        )

    # KPIs : calculés sur les mêmes tickets que le tableau
    nb_tickets      = tickets.count()
    total_collected = tickets.aggregate(s=Sum('montant_total'))['s'] or Decimal('0')

    # Avoirs uniquement liés aux tickets visibles (ticket_origine)
    ticket_ids   = tickets.values_list('id', flat=True)
    avoirs_qs    = Avoir.objects.filter(ticket_origine_id__in=ticket_ids)
    total_avoirs = avoirs_qs.aggregate(s=Sum('total'))['s'] or Decimal('0')
    nb_avoirs    = avoirs_qs.count()

    stats = {
        'tickets_today_count': nb_tickets,
        'total_collected':     total_collected,
        'total_avoirs':        total_avoirs,
        'nb_avoirs':           nb_avoirs,
        'net_total':           total_collected - total_avoirs,
    }

    context = {
        'tickets':        tickets,
        'module_choices': Ticket.MODULE_CHOICES,
        'module_filter':  module_filter,
        'date_debut':     date_debut_str,
        'date_fin':       date_fin_str,
        'query':          query,
        'stats':          stats,
        'today':          today,
    }
    return render(request, 'facturation/ticket_list.html', context)

@require_module_access('facturation')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'facturation/ticket_detail.html', {'ticket': ticket})

@require_superuser
@require_POST
def ticket_delete(request, pk):
    """
    Supprime définitivement un ticket : restaure le stock des articles vendus
    (restaurant, hôtel, cave, piscine) et supprime la transaction source
    (commande, réservation, vente, accès piscine) ainsi que les transactions
    liées (avoirs émis sur ce ticket). Action irréversible, réservée au
    Super Administrateur.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    numero = ticket.numero
    infos = []
    avertissement = ''

    try:
        with transaction.atomic():
            if ticket.module == 'restaurant' and ticket.objet_id:
                from restaurant.models import Commande
                from cuisine.utils import process_stock_movement
                from bar.models import MouvementStockBar
                commande = Commande.objects.filter(id=ticket.objet_id).first()
                if commande:
                    lignes = list(commande.lignes.select_related('plat', 'accompagnement', 'boisson').all())
                    for ligne in lignes:
                        process_stock_movement(
                            ligne.plat, ligne.quantite, 'entree', request.user,
                            f"Suppression Ticket {numero}"
                        )
                        if ligne.accompagnement:
                            process_stock_movement(
                                ligne.accompagnement, ligne.quantite, 'entree', request.user,
                                f"Suppression Ticket {numero}"
                            )
                        if ligne.boisson:
                            MouvementStockBar.objects.create(
                                boisson=ligne.boisson, type_mouvement='entree', quantite=ligne.quantite,
                                commentaire=f"Suppression Ticket {numero}", utilisateur=request.user,
                            )
                    if lignes:
                        infos.append("le stock des articles a été restauré")
                    table = commande.table
                    commande.delete()
                    if table:
                        autres_actives = Commande.objects.filter(
                            table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
                        ).exists()
                        if not autres_actives:
                            table.statut = 'disponible'
                            table.save(update_fields=['statut'])
                else:
                    avertissement = "La commande d'origine est introuvable — aucun stock n'a été modifié."

            elif ticket.module == 'hotel' and ticket.objet_id:
                from hotel.models import Reservation
                from cuisine.utils import process_stock_movement
                from bar.models import BoissonBar
                from django.db.models import F
                reservation = Reservation.objects.filter(id=ticket.objet_id).first()
                if reservation:
                    consos = list(reservation.consommations.all())
                    for conso in consos:
                        if conso.type_service == 'bar' and conso.boisson_id:
                            BoissonBar.objects.filter(pk=conso.boisson_id).update(
                                quantite_stock=F('quantite_stock') + conso.quantite
                            )
                        elif conso.type_service == 'restaurant' and conso.plat_id:
                            process_stock_movement(
                                conso.plat, conso.quantite, 'entree', request.user,
                                f"Suppression Ticket {numero}"
                            )
                    if consos:
                        infos.append("le stock des consommations a été restauré")
                        reservation.consommations.all().delete()
                    if reservation.statut == 'terminee':
                        reservation.statut = 'en_cours'
                        reservation.save(update_fields=['statut'])
                        if reservation.chambre and reservation.chambre.statut == 'disponible':
                            reservation.chambre.statut = 'occupee'
                            reservation.chambre.save(update_fields=['statut'])
                        infos.append("le séjour a été remis en cours")
                else:
                    avertissement = "La réservation d'origine est introuvable — aucun stock n'a été modifié."

            elif ticket.module == 'cave' and ticket.objet_id:
                from bar.models import VenteCave
                vente = VenteCave.objects.filter(id=ticket.objet_id).first()
                if vente:
                    lignes_cave = list(vente.lignes.select_related('boisson').all())
                    restaurees = 0
                    for ligne in lignes_cave:
                        if ligne.boisson:
                            ligne.boisson.restock(ligne.quantite, f"Suppression Ticket {numero}", request.user)
                            restaurees += 1
                    if restaurees:
                        infos.append("le stock des articles a été restauré")
                    if len(lignes_cave) > restaurees:
                        avertissement = (
                            "Certains articles de la vente n'ont pas pu être identifiés en stock "
                            "(article supprimé depuis) — vérifiez le stock manuellement."
                        )
                    vente.delete()
                else:
                    avertissement = "La vente d'origine est introuvable — aucun stock n'a été modifié."

            elif ticket.module == 'piscine' and ticket.objet_id:
                from piscine.models import AccesPiscine
                from bar.models import BoissonBar, MouvementStockBar
                from restaurant.models import PlatMenu
                from cuisine.utils import process_stock_movement
                acces = AccesPiscine.objects.filter(id=ticket.objet_id).first()
                if acces:
                    consos = list(acces.consommations.all())
                    restaurees = 0
                    for conso in consos:
                        boisson = BoissonBar.objects.filter(nom=conso.produit).first()
                        if boisson:
                            MouvementStockBar.objects.create(
                                boisson=boisson, type_mouvement='entree', quantite=conso.quantite,
                                commentaire=f"Suppression Ticket {numero}", utilisateur=request.user,
                            )
                            restaurees += 1
                            continue
                        plat = PlatMenu.objects.filter(nom=conso.produit).first()
                        if plat:
                            process_stock_movement(
                                plat, conso.quantite, 'entree', request.user,
                                f"Suppression Ticket {numero}"
                            )
                            restaurees += 1
                    if restaurees:
                        infos.append("le stock des articles a été restauré")
                    acces.delete()
                else:
                    avertissement = "L'accès piscine d'origine est introuvable — aucun stock n'a été modifié."

            elif ticket.module == 'espace' and ticket.objet_id:
                from espaces_evenementiels.models import ReservationEspace
                reservation_espace = ReservationEspace.objects.filter(id=ticket.objet_id).first()
                if reservation_espace:
                    reservation_espace.delete()
                    infos.append("la réservation d'espace a été supprimée")
                else:
                    avertissement = "La réservation d'espace d'origine est introuvable."
            else:
                avertissement = (
                    "Ce module ne permet pas de retrouver automatiquement les articles vendus : "
                    "vérifiez et ajustez le stock manuellement si nécessaire."
                )

            nb_avoirs = ticket.avoirs.count()
            if nb_avoirs:
                ticket.avoirs.all().delete()
                infos.append(f"{nb_avoirs} avoir(s) lié(s) supprimé(s)")

            Article.objects.filter(
                content_type=ContentType.objects.get_for_model(Ticket),
                object_id=ticket.id,
            ).delete()

            ticket.delete()

        msg = f"Ticket {numero} supprimé."
        if infos:
            msg += " " + ", ".join(infos).capitalize() + "."
        if avertissement:
            messages.warning(request, f"{msg} {avertissement}")
        else:
            messages.success(request, msg)

    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du ticket {numero} : {str(e)}")
        return redirect('facturation:ticket_detail', pk=pk)

    return redirect('facturation:ticket_list')

@require_module_access('facturation')
def ticket_reprint(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.mark_as_duplicata()
    return redirect('facturation:ticket_print_thermal', pk=ticket.pk)

@require_module_access('facturation')
def ticket_print_thermal(request, pk):
    """Afficher le ticket en format thermique (HTML)"""
    import re
    ticket = get_object_or_404(Ticket, pk=pk)
    serveur = ''

    # 1. Chercher dans le contenu HTML (nouveaux tickets)
    if ticket.contenu:
        match = re.search(r'data-serveur="([^"]*)"', ticket.contenu)
        if match:
            serveur = match.group(1)

    # 2. Chercher via la commande restaurant (objet_id)
    if not serveur and ticket.module == 'restaurant' and ticket.objet_id:
        try:
            from restaurant.models import Commande
            cmd = Commande.objects.select_related('serveur').filter(id=ticket.objet_id).first()
            if cmd and cmd.serveur:
                serveur = cmd.serveur.get_full_name() or cmd.serveur.username
        except Exception:
            pass

    # 3. Fallback: cree_par
    if not serveur and ticket.cree_par:
        serveur = ticket.cree_par.get_full_name() or ticket.cree_par.username

    return render(request, 'facturation/ticket_print_thermal.html', {
        'ticket': ticket,
        'serveur': serveur,
    })

@require_module_access('facturation')
def ticket_pdf(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    context = {
        'ticket': ticket,
        'nom_entreprise': NOM_ENTREPRISE,
        'adresse_entreprise': ADRESSE_ENTREPRISE,
        'telephone_entreprise': TELEPHONE_ENTREPRISE,
        'email_entreprise': EMAIL_ENTREPRISE,
        'logo_path': get_logo_path(),
    }

    html_string = render_to_string('facturation/ticket_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_{ticket.numero}.pdf"'
    return response

@require_module_access('facturation')
def create_avoir_from_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    
    try:
        with transaction.atomic():
            # 1. Identifier le service
            service_name = ticket.get_module_display()
            service = Service.objects.filter(nom__icontains=service_name).first()
            if not service:
                service = Service.objects.first()
            
            # 2. Créer ou récupérer un Article générique pour ce ticket
            content_type = ContentType.objects.get_for_model(Ticket)
            article, _ = Article.objects.get_or_create(
                content_type=content_type,
                object_id=ticket.id,
                defaults={'service': service}
            )
            
            # 3. Créer l'Avoir
            # Utiliser le client du ticket ou un client par défaut
            client = ticket.client
            if not client:
                client, _ = Client.objects.get_or_create(nom="Client Ticket", defaults={'telephone': 'N/A'})

            avoir = Avoir.objects.create(
                numero=Avoir.generate_numero(),
                ticket_origine=ticket,
                client=client,
                cree_par=request.user,
                motif=f"Remboursement Ticket {ticket.numero}",
                statut='accepted', # On suppose qu'un avoir créé depuis un ticket est validé immédiatement
                date_creation=timezone.now(),
                date_avoir=timezone.now().date()
            )
            
            # 4. Créer la ligne d'avoir
            LigneAvoir.objects.create(
                avoir=avoir,
                article=article,
                description=f"Remboursement Ticket #{ticket.numero}",
                quantite=Decimal('1'),
                prix_unitaire=ticket.montant_total,
                taux_remise=Decimal('0')
            )
            
            # 5. Calculer les totaux
            avoir.calculate_totals()
            
            messages.success(request, f"Avoir {avoir.numero} créé avec succès.")
            return redirect('facturation:avoir_pdf', pk=avoir.pk)
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de l'avoir: {str(e)}")
        return redirect('facturation:ticket_detail', pk=pk)

# API endpoints
@require_module_access('facturation')
def get_articles_by_service(request, service_id):
    try:
        service = Service.objects.get(id=service_id)
        articles = []
        
        # 1. Chambres (Hôtel)
        if service.nom.lower() in ["hébergement", "hôtel", "hotel"] or "chambre" in service.nom.lower():
            # On exclut seulement les chambres en maintenance, car on peut vouloir facturer une chambre occupée
            for chambre in Chambre.objects.exclude(statut='maintenance'):
                articles.append({
                    'id': chambre.id,
                    'name': f"Chambre {chambre.numero} ({chambre.get_type_chambre_display()})",
                    'price': float(chambre.prix_nuit),
                    'content_type_id': ContentType.objects.get_for_model(Chambre).id,
                    'object_id': chambre.id
                })
                
        # 2. Cave (Anciennement Bar - Boissons uniquement)
        elif "cave" in service.nom.lower() or "bar" in service.nom.lower():
            drink_keywords = ['boisson', 'bière', 'biere', 'vin', 'alcool', 'champagne', 'liqueur', 'whisky', 'vodka', 'gin', 'soda', 'jus', 'eau', 'café', 'the', 'thé', 'cocktail', 'aperitif', 'digestif']
            query = Q()
            for keyword in drink_keywords:
                query |= Q(categorie__nom__icontains=keyword)
            
            # On cherche aussi les catégories qui contiennent "Bar" ou "Cave"
            query |= Q(categorie__nom__icontains="bar")
            query |= Q(categorie__nom__icontains="cave")

            for plat in PlatMenu.objects.filter(query, disponible=True):
                articles.append({
                    'id': plat.id,
                    'name': f"{plat.nom} ({plat.categorie.nom})",
                    'price': float(plat.prix),
                    'content_type_id': ContentType.objects.get_for_model(PlatMenu).id,
                    'object_id': plat.id
                })

        # 3. Restaurant (Nourriture, exclusion des boissons de la Cave)
        elif service.nom.lower() in ["restauration", "restaurant"] or "restaurant" in service.nom.lower():
            drink_keywords = ['boisson', 'bière', 'biere', 'vin', 'alcool', 'champagne', 'liqueur', 'whisky', 'vodka', 'gin', 'soda', 'jus', 'eau', 'café', 'the', 'thé', 'cocktail', 'aperitif', 'digestif']
            query = Q()
            for keyword in drink_keywords:
                query |= Q(categorie__nom__icontains=keyword)
            
            # On exclut aussi les catégories "Bar" et "Cave"
            query |= Q(categorie__nom__icontains="bar")
            query |= Q(categorie__nom__icontains="cave")

            for plat in PlatMenu.objects.filter(disponible=True).exclude(query):
                articles.append({
                    'id': plat.id,
                    'name': f"{plat.nom} ({plat.categorie.nom})",
                    'price': float(plat.prix),
                    'content_type_id': ContentType.objects.get_for_model(PlatMenu).id,
                    'object_id': plat.id
                })
                
        # 3. Espaces Événementiels
        elif "espace" in service.nom.lower() or "salle" in service.nom.lower() or "location" in service.nom.lower():
            for espace in EspaceEvenementiel.objects.all():
                articles.append({
                    'id': espace.id,
                    'name': f"{espace.nom} ({espace.capacite} pers.)",
                    'price': float(espace.prix_jour),
                    'content_type_id': ContentType.objects.get_for_model(EspaceEvenementiel).id,
                    'object_id': espace.id
                })
        
        # 4. Fallback (Services génériques ou autres)
        # Si on avait un modèle "Produit" générique, on l'ajouterait ici.
        
        return JsonResponse({'articles': articles})
    except Service.DoesNotExist:
        return JsonResponse({'articles': []}, status=404)

@require_module_access('facturation')
def client_detail_api(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    data = {
        'id': client.id,
        'nom': client.nom,
        'email': client.email,
        'telephone': client.telephone,
        'adresse': client.adresse,
    }
    return JsonResponse(data)

@require_module_access('facturation')
def create_document(request, doc_type):
    if doc_type == 'facture':
        return facture_create(request)
    elif doc_type == 'proforma':
        return proforma_create(request)
    elif doc_type == 'avoir':
        return avoir_create(request)
    elif doc_type == 'facture_from_ticket':
        return facture_from_ticket(request)
    return JsonResponse({'success': False, 'error': 'Type de document invalide'})


def _parser_contenu_ticket(contenu):
    """Parse le contenu d'un ticket et retourne une liste de (designation, prix)."""
    if not contenu:
        return []
    
    lignes = []
    
    # Format HTML : <div class="row"><span class="item-name">...</span><span class="item-price">...</span></div>
    if '<div class="row">' in contenu or '<div class=' in contenu:
        from html.parser import HTMLParser
        import re
        # Extraire les paires item-name / item-price
        noms = re.findall(r'<span[^>]*class=[^>]*item-name[^>]*>(.*?)</span>', contenu, re.DOTALL)
        prix = re.findall(r'<span[^>]*class=[^>]*item-price[^>]*>(.*?)</span>', contenu, re.DOTALL)
        for i, nom in enumerate(noms):
            nom_clean = re.sub(r'<[^>]+>', '', nom).strip()
            if not nom_clean:
                continue
            prix_val = Decimal('0')
            if i < len(prix):
                prix_str = re.sub(r'[^\d,.]', '', prix[i].replace(',', '').replace(' ','').strip())
                try:
                    prix_val = Decimal(prix_str) if prix_str else Decimal('0')
                except Exception:
                    prix_val = Decimal('0')
            lignes.append((nom_clean, prix_val))
    
    else:
        # Format texte brut Cave : "  Article x1  1,000 F"
        import re
        for line in contenu.split('\n'):
            line = line.strip()
            if not line or line.startswith('=') or line.startswith('TOTAL') or line.startswith('Reglement') or line.startswith('Recu') or line.startswith('Rendu') or line.startswith('COMPLEXE') or line.startswith('Ticket') or line.startswith('Date') or line.startswith('Espace') or line.startswith('Ref'):
                continue
            # Pattern : "Nom article x2  1,500 F"
            match = re.match(r'^(.+?)\s+([\d,\s]+)\s*F\s*$', line)
            if match:
                nom = match.group(1).strip()
                prix_str = match.group(2).replace(',', '').replace(' ', '').strip()
                try:
                    prix_val = Decimal(prix_str)
                    lignes.append((nom, prix_val))
                except Exception:
                    pass
    
    return lignes


def facture_from_ticket(request):
    """Convertir un ticket en facture."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    try:
        data = json.loads(request.body)
        ticket_id  = data.get('ticket_id')
        client_name = data.get('client_name', '').strip()
        client_phone = data.get('client_phone', '').strip()
        date_echeance = data.get('date_echeance') or None
        notes = data.get('notes', '').strip()

        if not ticket_id or not client_name:
            return JsonResponse({'success': False, 'error': 'Champs requis manquants'})

        ticket = get_object_or_404(Ticket, id=ticket_id)

        # Créer ou récupérer le client
        client, _ = Client.objects.get_or_create(
            nom=client_name,
            defaults={'telephone': client_phone}
        )
        if client_phone and not client.telephone:
            client.telephone = client_phone
            client.save()

        # Générer numéro facture
        from django.utils import timezone as tz
        annee = tz.now().year
        last = Facture.objects.filter(numero__startswith=f'FAC-{annee}-').order_by('numero').last()
        seq = int(last.numero.split('-')[-1]) + 1 if last else 1
        numero = f'FAC-{annee}-{seq:04d}'

        # Créer la facture
        from datetime import date, timedelta
        echeance = None
        if date_echeance:
            from django.utils.dateparse import parse_date
            echeance = parse_date(date_echeance)

        facture = Facture.objects.create(
            numero=numero,
            client=client,
            date_facturation=date.today(),
            date_echeance=echeance or (date.today() + timedelta(days=30)),
            statut='payee',
            sous_total=ticket.montant_total,
            remise=0,
            taux_tva=0,
            montant_tva=0,
            total=ticket.montant_total,
            montant_paye=ticket.montant_paye,
            date_paiement=ticket.date_creation,
            notes=f"Converti depuis ticket {ticket.numero}" + (f" — {notes}" if notes else ""),
            cree_par=request.user,
        )

        # Créer une ligne facture avec le contenu du ticket
        # Parser le contenu du ticket pour créer une ligne par article
        lignes_parsed = _parser_contenu_ticket(ticket.contenu)
        
        if lignes_parsed:
            for designation, prix in lignes_parsed:
                LigneFacture.objects.create(
                    facture=facture,
                    article=None,
                    designation=designation,
                    quantite=1,
                    prix_unitaire=prix,
                )
        else:
            # Fallback : une seule ligne avec le total
            LigneFacture.objects.create(
                facture=facture,
                article=None,
                designation=f"{ticket.get_module_display()} — {ticket.numero}",
                quantite=1,
                prix_unitaire=ticket.montant_total,
            )

        return JsonResponse({
            'success': True,
            'message': f'Facture {numero} créée',
            'facture_id': facture.id,
            'detail_url': f'/facturation/factures/{facture.id}/',
        })
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e)})

@require_module_access('facturation')
def get_document_details(request, doc_type, pk):
    try:
        if doc_type == 'proforma':
            doc = get_object_or_404(Proforma, pk=pk)
            lines = doc.lignes.all()
        elif doc_type == 'facture':
            doc = get_object_or_404(Facture, pk=pk)
            lines = doc.lignes.all()
        else:
             return JsonResponse({'success': False, 'error': 'Type de document invalide'})
        
        articles_data = []
        for line in lines:
            # Reconstruct the composite ID for the select box
            composite_id = f"{line.article.content_type.id}:{line.article.object_id}"
            
            # Try to get a readable name
            try:
                item_name = str(line.article.content_object)
            except:
                item_name = "Article inconnu"

            articles_data.append({
                'service_id': line.article.service.id,
                'composite_id': composite_id,
                'name': item_name,
                'quantity': float(line.quantite),
                'price': float(line.prix_unitaire)
            })

        data = {
            'id': doc.pk,
            'numero': doc.numero,
            'client_name': doc.client.nom,
            'client_phone': doc.client.telephone,
            'client_email': doc.client.email,
            'client_address': doc.client.adresse,
            'remise': float(doc.remise),
            'tva': float(doc.taux_tva),
            'articles': articles_data
        }
        return JsonResponse({'success': True, 'document': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def receipt_depot(request):
    """Page de reçu de dépôt universel (chambre)."""
    return render(request, 'receipt_depot.html')
