from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TableBoite, Evenement, EntreeBoite, ConsommationBoite
from django.utils import timezone

@login_required
def boite_nuit_index(request):
    """Vue principale de la boîte de nuit"""
    
    # Statistiques du jour
    today = timezone.now().date()
    entrees_jour = EntreeBoite.objects.filter(date_entree__date=today).count()
    
    # Tables
    tables = TableBoite.objects.all()
    tables_disponibles = tables.filter(statut='disponible').count()
    tables_occupees = tables.filter(statut='occupee').count()
    tables_vip = tables.filter(type_table='vip').count()
    
    # Recette du jour
    recette_entrees = sum(
        entree.prix_entree * entree.nombre_personnes 
        for entree in EntreeBoite.objects.filter(date_entree__date=today)
    )
    recette_consommations = sum(
        conso.total 
        for conso in ConsommationBoite.objects.filter(date_creation__date=today)
    )
    recette_totale = recette_entrees + recette_consommations
    
    # Événement du jour
    evenement_jour = Evenement.objects.filter(date_evenement=today).first()
    
    # Liste des entrées
    entrees_liste = EntreeBoite.objects.filter(date_entree__date=today).order_by('-date_entree')
    
    context = {
        'entrees_jour': entrees_jour,
        'tables_disponibles': tables_disponibles,
        'tables_occupees': tables_occupees,
        'tables_vip': tables_vip,
        'recette_totale': recette_totale,
        'evenement_jour': evenement_jour,
        'entrees_liste': entrees_liste,
        'tables': tables,
    }
    
    return render(request, 'boite_nuit/index.html', context)