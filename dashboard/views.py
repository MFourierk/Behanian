from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """Vue du tableau de bord principal"""
    
    # Données temporaires (à remplacer par les vraies données plus tard)
    context = {
        'chiffre_affaires': 0,
        'variation': '+12%',
        'taux_occupation': 17,
        'chambres_occupees': 1,
        'total_chambres': 6,
        'reservations_actives': 0,
        'alertes_stock': 1,
        'user': request.user,
    }
    
    return render(request, 'dashboard/dashboard.html', context)