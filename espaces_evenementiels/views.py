from utils.permissions import require_module_access
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import EspaceEvenementiel, ReservationEspace

@require_module_access('espaces')
def espaces_index(request):
    """Vue principale des espaces événementiels"""
    
    # Liste des espaces
    espaces = EspaceEvenementiel.objects.all()
    
    # Réservations
    reservations = ReservationEspace.objects.filter(statut__in=['confirmee', 'en_cours'])
    
    context = {
        'espaces': espaces,
        'reservations': reservations,
    }
    
    return render(request, 'espaces_evenementiels/index.html', context)