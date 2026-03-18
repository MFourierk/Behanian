from utils.permissions import require_module_access
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AccesPiscine, TarifPiscine
from django.utils import timezone

@require_module_access('piscine')
def piscine_index(request):
    """Vue principale de la piscine"""
    
    # Statistiques du jour
    today = timezone.now().date()
    entrees_jour = AccesPiscine.objects.filter(date_entree__date=today).count()
    
    # Accès actuellement actifs (pas encore sortis)
    acces_actifs = AccesPiscine.objects.filter(date_sortie__isnull=True)
    actuellement = acces_actifs.count()
    
    # Visiteurs et hébergés
    visiteurs = acces_actifs.filter(type_client='visiteur').count()
    heberges = acces_actifs.filter(type_client='heberge').count()
    
    # Recette du jour
    recette_jour = sum(
        acces.prix_total for acces in AccesPiscine.objects.filter(date_entree__date=today)
    )
    
    # Liste des accès du jour
    acces_liste = AccesPiscine.objects.filter(date_entree__date=today).order_by('-date_entree')
    
    context = {
        'entrees_jour': entrees_jour,
        'actuellement': actuellement,
        'visiteurs': visiteurs,
        'heberges': heberges,
        'recette_jour': recette_jour,
        'acces_liste': acces_liste,
    }
    
    return render(request, 'piscine/index.html', context)