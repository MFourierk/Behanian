from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CaisseSession
from django.contrib import messages
from django.utils import timezone

@login_required
def index(request):
    if request.method == 'POST':
        # Logique pour ouvrir la caisse
        caisse_ouverte = CaisseSession.objects.filter(user=request.user, is_open=True).first()
        if not caisse_ouverte:
            CaisseSession.objects.create(user=request.user)
            messages.success(request, "La caisse a été ouverte avec succès.")
        else:
            messages.warning(request, "Vous avez déjà une caisse ouverte.")
        return redirect('caisse:index')

    caisse_ouverte = CaisseSession.objects.filter(user=request.user, is_open=True).first()
    context = {
        'caisse_ouverte': caisse_ouverte
    }
    return render(request, 'caisse/index.html', context)

@login_required
def fermer_caisse(request):
    if request.method == 'POST':
        caisse_ouverte = CaisseSession.objects.filter(user=request.user, is_open=True).first()
        if caisse_ouverte:
            caisse_ouverte.is_open = False
            caisse_ouverte.closed_at = timezone.now()
            caisse_ouverte.save()
            messages.success(request, "La caisse a été fermée avec succès.")
        else:
            messages.warning(request, "Aucune caisse n'est actuellement ouverte.")
    return redirect('caisse:index')


