from utils.permissions import require_module_access
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
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
    factures_impayees = Facture.objects.filter(statut__in=['envoyee','en_attente'])
    montant_impaye = factures_impayees.aggregate(s=Sum('total'))['s'] or 0

    # Tickets récents tous modules
    tickets_recents = Ticket.objects.select_related('client','cree_par').order_by('-date_creation')[:10]

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
    factures = Facture.objects.all()
    return render(request, 'facturation/facture_list.html', {'factures': factures})

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
    proformas = Proforma.objects.all()
    return render(request, 'facturation/proforma_list.html', {'proformas': proformas})

@require_module_access('facturation')
def proforma_create(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Gérer le client
                client_name = request.POST.get('client_name')
                client_phone = request.POST.get('client_phone')
                client_email = request.POST.get('client_email')
                client_address = request.POST.get('client_address') # Assurez-vous que ce champ existe si nécessaire

                client, created = Client.objects.get_or_create(
                    nom=client_name,
                    defaults={
                        'telephone': client_phone,
                        'email': client_email,
                        'adresse': client_address or ''
                    }
                )

                # 2. Créer l'objet Proforma principal
                date_creation_str = request.POST.get('date_creation')
                if date_creation_str:
                    date_creation = timezone.datetime.strptime(date_creation_str, '%Y-%m-%d')
                    # Make it timezone aware if naive
                    if timezone.is_naive(date_creation):
                        date_creation = timezone.make_aware(date_creation)
                else:
                    date_creation = timezone.now()
                
                # Validité par défaut de 15 jours
                date_validite = date_creation.date() + timedelta(days=15)

                proforma = Proforma.objects.create(
                    client=client,
                    cree_par=request.user,
                    remise=Decimal(request.POST.get('remise', 0)),
                    taux_tva=Decimal(request.POST.get('tva', 0)), # Le champ s'appelle 'tva' dans le form
                    date_creation=date_creation,
                    date_validite=date_validite
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

                            LigneProforma.objects.create(
                                proforma=proforma,
                                article=article_wrapper,
                                quantite=Decimal(quantity),
                                prix_unitaire=Decimal(price)
                            )
                        except (ValueError, Service.DoesNotExist, ContentType.DoesNotExist) as e:
                            # Log l'erreur et continuer
                            print(f"Skipping invalid article line: {i}. Error: {e}")
                    
                    i += 1

                # 4. Calculer les totaux
                proforma.calculate_totals()
                
                pdf_url = reverse('facturation:proforma_pdf', kwargs={'pk': proforma.pk})
                return JsonResponse({'success': True, 'pdf_url': pdf_url})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@require_module_access('facturation')
def proforma_detail(request, pk):
    proforma = get_object_or_404(Proforma, pk=pk)
    return render(request, 'facturation/proforma_detail.html', {'proforma': proforma})

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
    avoirs = Avoir.objects.all()
    return render(request, 'facturation/avoir_list.html', {'avoirs': avoirs})

@require_module_access('facturation')
def avoir_create(request):
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

                # 2. Créer l'objet Avoir principal
                date_creation_str = request.POST.get('date_creation')
                if date_creation_str:
                    date_creation = timezone.datetime.strptime(date_creation_str, '%Y-%m-%d')
                    if timezone.is_naive(date_creation):
                        date_creation = timezone.make_aware(date_creation)
                else:
                    date_creation = timezone.now()

                avoir = Avoir.objects.create(
                    client=client,
                    cree_par=request.user,
                    motif=request.POST.get('motif', 'Avoir standard'),
                    remise=Decimal(request.POST.get('remise', 0)),
                    taux_tva=Decimal(request.POST.get('tva', 0)),
                    date_creation=date_creation,
                    date_avoir=date_creation.date()
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

                            LigneAvoir.objects.create(
                                avoir=avoir,
                                article=article_wrapper,
                                quantite=Decimal(quantity),
                                prix_unitaire=Decimal(price)
                            )
                        except (ValueError, Service.DoesNotExist, ContentType.DoesNotExist) as e:
                            print(f"Skipping invalid article line: {i}. Error: {e}")
                    
                    i += 1

                # 4. Calculer les totaux
                avoir.calculate_totals()
                
                pdf_url = reverse('facturation:avoir_pdf', kwargs={'pk': avoir.pk})
                return JsonResponse({'success': True, 'pdf_url': pdf_url})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
    
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = today

    tickets = Ticket.objects.filter(date_creation__date=selected_date, imprime=True).order_by('-date_creation')

    service_filter = request.GET.get('service')
    if service_filter:
        tickets = tickets.filter(service__id=service_filter)

    query = request.GET.get('q')
    if query:
        tickets = tickets.filter(
            Q(numero__icontains=query) | Q(client__nom__icontains=query)
        )

    tickets_today_count = tickets.count()
    
    total_collected = tickets.aggregate(total=Sum('montant_total'))['total'] or Decimal('0')
    
    total_avoirs = Avoir.objects.filter(date_creation__date=selected_date).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    net_total = total_collected - total_avoirs

    stats = {
        'tickets_today_count': tickets_today_count,
        'total_collected': total_collected,
        'total_avoirs': total_avoirs,
        'net_total': net_total,
    }

    services = Service.objects.all()

    context = {
        'tickets': tickets,
        'services': services,
        'stats': stats,
        'today': selected_date,
    }
    return render(request, 'facturation/ticket_list.html', context)

@require_module_access('facturation')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'facturation/ticket_detail.html', {'ticket': ticket})

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
                    'name': espace.nom,
                    'price': float(espace.capacite), # Prix par défaut ou capacité? À vérifier. Mettons capacité pour l'instant ou 0.
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
