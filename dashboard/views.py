from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from utils.permissions import get_accessible_modules


@login_required
def dashboard_view(request):
    today = timezone.now().date()
    modules = get_accessible_modules(request.user)

    # Stats selon modules accessibles
    chiffre_affaires = 0
    taux_occupation  = 0
    chambres_occupees = 0
    total_chambres   = 0
    reservations_actives = 0
    alertes_stock    = 0

    try:
        from facturation.models import Ticket
        tickets_jour = Ticket.objects.filter(date_creation__date=today)

        # Filtrer par modules accessibles
        if '*' not in modules:
            mod_map = {'hotel':'hotel','restaurant':'restaurant','bar':'bar','piscine':'piscine'}
            allowed = [mod_map[m] for m in modules if m in mod_map]
            tickets_jour = tickets_jour.filter(module__in=allowed)

        chiffre_affaires = int(tickets_jour.aggregate(s=Sum('montant_total'))['s'] or 0)
    except Exception:
        pass

    if 'hotel' in modules:
        try:
            from hotel.models import Chambre, Reservation
            total_chambres    = Chambre.objects.count()
            chambres_occupees = Chambre.objects.filter(statut='occupee').count()
            taux_occupation   = round((chambres_occupees / total_chambres * 100) if total_chambres else 0)
            reservations_actives = Reservation.objects.filter(statut__in=['en_attente','confirmee','en_cours']).count()
        except Exception:
            pass

    if 'cuisine' in modules or '*' in modules:
        try:
            from cuisine.models import Ingredient
            alertes_stock = Ingredient.objects.filter(quantite_stock__lte=5).count()
        except Exception:
            pass

    context = {
        'chiffre_affaires':    chiffre_affaires,
        'variation':           '+0%',
        'taux_occupation':     taux_occupation,
        'chambres_occupees':   chambres_occupees,
        'total_chambres':      total_chambres,
        'reservations_actives':reservations_actives,
        'alertes_stock':       alertes_stock,
        'user':                request.user,
        'today':               today,
    }
    return render(request, 'dashboard/dashboard.html', context)
