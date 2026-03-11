# cuisine/views_reports.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, CharField
from django.db.models.functions import Coalesce
from .models import MouvementStock, Ingredient
from django.utils import timezone
from datetime import timedelta

@login_required
def rapport_consommation(request):
    """Rapport sur la consommation des articles (sorties de stock)."""
    today = timezone.now().date()
    start_date_str = request.GET.get('start_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Mouvements de sortie (cuisine, service)
    consommation_data = MouvementStock.objects.filter(
        type_mouvement='sortie',
        date__date__range=[start_date, end_date]
    ).values(
        nom=F('ingredient__nom'), unite=F('ingredient__unite')
    ).annotate(
        quantite_totale=Sum('quantite'),
        valeur_totale=Sum(F('quantite') * F('ingredient__prix_moyen'))
    ).order_by('-valeur_totale')

    total_valeur_consommee = consommation_data.aggregate(total=Sum('valeur_totale'))['total'] or 0

    context = {
        'consommation_data': consommation_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_valeur_consommee': total_valeur_consommee,
        'page_title': 'Rapport de Consommation'
    }
    return render(request, 'cuisine/rapport_template.html', context)

# --- Vues API pour les graphiques ---
from django.http import JsonResponse

@login_required
def chart_data_mouvements(request):
    """Données pour le graphique de répartition des mouvements."""
    mouvements = MouvementStock.objects.values('type_mouvement').annotate(count=Sum('quantite')).order_by()
    
    labels = [m['type_mouvement'] for m in mouvements]
    data = [m['count'] for m in mouvements]
    
    return JsonResponse({'labels': labels, 'data': data})

@login_required
def chart_data_top_consommation(request):
    """Données pour le graphique du top 5 des articles consommés."""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)

    consommation = MouvementStock.objects.filter(
        type_mouvement='sortie',
        date__date__gte=start_date
    ).values(nom=F('ingredient__nom')).annotate(
        valeur=Sum(F('quantite') * F('ingredient__prix_moyen'))
    ).order_by('-valeur')[:5]

    labels = [c['nom'] for c in consommation]
    data = [c['valeur'] for c in consommation]

    return JsonResponse({'labels': labels, 'data': data})

@login_required
def rapport_pertes(request):
    """Rapport sur les pertes et prélèvements."""
    today = timezone.now().date()
    start_date_str = request.GET.get('start_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Mouvements de pertes et prélèvements
    pertes_data = MouvementStock.objects.filter(
        type_mouvement__in=['perte', 'prelevement'],
        date__date__range=[start_date, end_date]
    ).values(
        nom=F('ingredient__nom'), unite=F('ingredient__unite'), type_mouvement=F('type_mouvement')
    ).annotate(
        quantite_totale=Sum('quantite'),
        valeur_totale=Sum(F('quantite') * F('ingredient__prix_moyen'))
    ).order_by('-date')

    total_valeur_perdue = pertes_data.aggregate(total=Sum('valeur_totale'))['total'] or 0

    context = {
        'consommation_data': pertes_data, # Réutilisation du nom de variable du template
        'start_date': start_date,
        'end_date': end_date,
        'total_valeur_consommee': total_valeur_perdue, # Réutilisation
        'page_title': 'Rapport des Pertes & Prélèvements'
    }
    return render(request, 'cuisine/rapport_template.html', context)

@login_required
def rapports_dashboard(request):
    """Page principale des rapports et analyses visuelles."""
    return render(request, 'cuisine/rapports_dashboard.html')
