from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import BonCommandeBar, BoissonBar

@login_required
def bar_dashboard(request):
    """Vue principale du nouveau module Bar/Cave."""
    context = {
        'page_title': 'Tableau de Bord du Bar'
    }
    return render(request, 'bar/dashboard.html', context)

@login_required
def stock_management(request):
    context = {
        'page_title': 'Gestion du Stock (Bar)'
    }
    return render(request, 'bar/stock_management.html', context)

class BonCommandeBarListView(ListView):
    model = BonCommandeBar
    template_name = 'bar/bon_commande_list.html'
    context_object_name = 'bons_de_commande'
    ordering = ['-date_commande']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Bons de Commande (Bar)'
        return context
