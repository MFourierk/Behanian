from utils.permissions import require_module_access, require_manager
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator

from hotel.models import Chambre
from restaurant.models import Table, PlatMenu, CategorieMenu
from espaces_evenementiels.models import EspaceEvenementiel
from bar.models import BoissonBar, CategorieBar, TableBar

from django.http import HttpResponse

@require_manager
def parametres_index(request):
    return render(request, 'parametres/index.html')

# --- BAR : BOISSONS ---
@method_decorator(login_required, name='dispatch')
class BoissonBarListView(ListView):
    model = BoissonBar
    template_name = 'parametres/boissonbar_list.html'
    context_object_name = 'boissons'

@method_decorator(login_required, name='dispatch')
class BoissonBarCreateView(CreateView):
    model = BoissonBar
    template_name = 'parametres/boissonbar_form.html'
    fields = ['nom', 'categorie', 'prix', 'image', 'quantite_stock', 'seuil_alerte', 'disponible', 'description']
    success_url = reverse_lazy('parametres:boissonbar_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Boisson créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class BoissonBarUpdateView(UpdateView):
    model = BoissonBar
    template_name = 'parametres/boissonbar_form.html'
    fields = ['nom', 'categorie', 'prix', 'image', 'quantite_stock', 'seuil_alerte', 'disponible', 'description']
    success_url = reverse_lazy('parametres:boissonbar_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Boisson modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class BoissonBarDeleteView(DeleteView):
    model = BoissonBar
    template_name = 'parametres/boissonbar_confirm_delete.html'
    success_url = reverse_lazy('parametres:boissonbar_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Boisson supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- BAR : CATEGORIES ---
@method_decorator(login_required, name='dispatch')
class CategorieBarListView(ListView):
    model = CategorieBar
    template_name = 'parametres/categoriebar_list.html'
    context_object_name = 'categories'

@method_decorator(login_required, name='dispatch')
class CategorieBarCreateView(CreateView):
    model = CategorieBar
    template_name = 'parametres/categoriebar_form.html'
    fields = ['nom']
    success_url = reverse_lazy('parametres:categoriebar_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Catégorie créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CategorieBarUpdateView(UpdateView):
    model = CategorieBar
    template_name = 'parametres/categoriebar_form.html'
    fields = ['nom']
    success_url = reverse_lazy('parametres:categoriebar_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Catégorie modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CategorieBarDeleteView(DeleteView):
    model = CategorieBar
    template_name = 'parametres/categoriebar_confirm_delete.html'
    success_url = reverse_lazy('parametres:categoriebar_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Catégorie supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- BAR : TABLES ---
@method_decorator(login_required, name='dispatch')
class TableBarListView(ListView):
    model = TableBar
    template_name = 'parametres/tablebar_list.html'
    context_object_name = 'tables'

@method_decorator(login_required, name='dispatch')
class TableBarCreateView(CreateView):
    model = TableBar
    template_name = 'parametres/tablebar_form.html'
    fields = ['numero', 'capacite', 'statut', 'zone']
    success_url = reverse_lazy('parametres:tablebar_list')

    def form_valid(self, form):
        messages.success(self.request, "Table créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TableBarUpdateView(UpdateView):
    model = TableBar
    template_name = 'parametres/tablebar_form.html'
    fields = ['numero', 'capacite', 'statut', 'zone']
    success_url = reverse_lazy('parametres:tablebar_list')

    def form_valid(self, form):
        messages.success(self.request, "Table modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TableBarDeleteView(DeleteView):
    model = TableBar
    template_name = 'parametres/tablebar_confirm_delete.html'
    success_url = reverse_lazy('parametres:tablebar_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Table supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- HOTEL : CHAMBRES ---
@method_decorator(login_required, name='dispatch')
class ChambreListView(ListView):
    model = Chambre
    template_name = 'parametres/chambre_list.html'
    context_object_name = 'chambres'

@method_decorator(login_required, name='dispatch')
class ChambreCreateView(CreateView):
    model = Chambre
    template_name = 'parametres/chambre_form.html'
    fields = '__all__'
    success_url = reverse_lazy('parametres:chambre_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Chambre créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ChambreUpdateView(UpdateView):
    model = Chambre
    template_name = 'parametres/chambre_form.html'
    fields = '__all__'
    success_url = reverse_lazy('parametres:chambre_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Chambre modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ChambreDeleteView(DeleteView):
    model = Chambre
    template_name = 'parametres/chambre_confirm_delete.html'
    success_url = reverse_lazy('parametres:chambre_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Chambre supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- RESTAURANT : TABLES ---
@method_decorator(login_required, name='dispatch')
class TableListView(ListView):
    model = Table
    template_name = 'parametres/table_list.html'
    context_object_name = 'tables'

@method_decorator(login_required, name='dispatch')
class TableCreateView(CreateView):
    model = Table
    template_name = 'parametres/table_form.html'
    fields = ['numero', 'capacite', 'statut', 'zone']
    success_url = reverse_lazy('parametres:table_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Table créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TableUpdateView(UpdateView):
    model = Table
    template_name = 'parametres/table_form.html'
    fields = ['numero', 'capacite', 'statut', 'zone']
    success_url = reverse_lazy('parametres:table_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Table modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TableDeleteView(DeleteView):
    model = Table
    template_name = 'parametres/table_confirm_delete.html'
    success_url = reverse_lazy('parametres:table_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Table supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- RESTAURANT : CATEGORIES ---
@method_decorator(login_required, name='dispatch')
class CategorieListView(ListView):
    model = CategorieMenu
    template_name = 'parametres/categorie_list.html'
    context_object_name = 'categories'

@method_decorator(login_required, name='dispatch')
class CategorieCreateView(CreateView):
    model = CategorieMenu
    template_name = 'parametres/categorie_form.html'
    fields = ['nom', 'ordre']
    success_url = reverse_lazy('parametres:categorie_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Catégorie de menu créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CategorieUpdateView(UpdateView):
    model = CategorieMenu
    template_name = 'parametres/categorie_form.html'
    fields = ['nom', 'ordre']
    success_url = reverse_lazy('parametres:categorie_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Catégorie de menu modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CategorieDeleteView(DeleteView):
    model = CategorieMenu
    template_name = 'parametres/categorie_confirm_delete.html'
    success_url = reverse_lazy('parametres:categorie_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Catégorie de menu supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --- RESTAURANT : PLATS ---
@method_decorator(login_required, name='dispatch')
class PlatListView(ListView):
    model = PlatMenu
    template_name = 'parametres/plat_list.html'
    context_object_name = 'plats'

@method_decorator(login_required, name='dispatch')
class PlatCreateView(CreateView):
    model = PlatMenu
    template_name = 'parametres/plat_form.html'
    fields = ['nom', 'categorie', 'prix', 'description', 'temps_preparation', 'disponible', 'image']
    success_url = reverse_lazy('parametres:plat_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Plat créé avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class PlatUpdateView(UpdateView):
    model = PlatMenu
    template_name = 'parametres/plat_form.html'
    fields = ['nom', 'categorie', 'prix', 'description', 'temps_preparation', 'disponible', 'image']
    success_url = reverse_lazy('parametres:plat_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Plat modifié avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class PlatDeleteView(DeleteView):
    model = PlatMenu
    template_name = 'parametres/plat_confirm_delete.html'
    success_url = reverse_lazy('parametres:plat_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Plat supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


# --- ESPACES ---
@method_decorator(login_required, name='dispatch')
class EspaceListView(ListView):
    model = EspaceEvenementiel
    template_name = 'parametres/espace_list.html'
    context_object_name = 'espaces'

EQUIP_LIST = [
    ('wifi','WiFi','📶'),('climatisation','Climatisation','❄️'),
    ('projecteur','Projecteur','📽️'),('sonorisation','Sonorisation','🔊'),
    ('decoration','Décoration','🎀'),('eclairage','Éclairage','💡'),
    ('tentes','Tentes','⛺'),('parking','Parking','🅿️'),
]

@method_decorator(login_required, name='dispatch')
class EspaceCreateView(CreateView):
    model = EspaceEvenementiel
    template_name = 'parametres/espace_form.html'
    fields = ['nom', 'type_espace', 'capacite', 'prix_jour', 'superficie', 'description', 'image', 'projecteur', 'wifi', 'climatisation', 'sonorisation', 'decoration', 'eclairage', 'tentes', 'parking', 'statut']
    success_url = reverse_lazy('parametres:espace_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['equip_list'] = EQUIP_LIST
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Espace créé avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class EspaceUpdateView(UpdateView):
    model = EspaceEvenementiel
    template_name = 'parametres/espace_form.html'
    fields = ['nom', 'type_espace', 'capacite', 'prix_jour', 'superficie', 'description', 'image', 'projecteur', 'wifi', 'climatisation', 'sonorisation', 'decoration', 'eclairage', 'tentes', 'parking', 'statut']
    success_url = reverse_lazy('parametres:espace_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['equip_list'] = EQUIP_LIST
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Espace modifié avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class EspaceDeleteView(DeleteView):
    model = EspaceEvenementiel
    template_name = 'parametres/espace_confirm_delete.html'
    success_url = reverse_lazy('parametres:espace_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Espace supprimé avec succès.")
        return super().delete(request, *args, **kwargs)