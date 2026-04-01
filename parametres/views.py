from utils.permissions import require_module_access, require_manager
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator

from hotel.models import Chambre
from restaurant.models import Table, PlatMenu, CategorieMenu
from espaces_evenementiels.models import EspaceEvenementiel
from bar.models import BoissonBar, CategorieBar, TableBar

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

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
    fields = ['nom', 'type_espace', 'capacite', 'prix_jour', 'prix_demi_journee', 'superficie', 'description', 'image', 'projecteur', 'wifi', 'climatisation', 'sonorisation', 'decoration', 'eclairage', 'tentes', 'parking', 'statut']
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
    fields = ['nom', 'type_espace', 'capacite', 'prix_jour', 'prix_demi_journee', 'superficie', 'description', 'image', 'projecteur', 'wifi', 'climatisation', 'sonorisation', 'decoration', 'eclairage', 'tentes', 'parking', 'statut']
    success_url = reverse_lazy('parametres:espace_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['equip_list'] = EQUIP_LIST
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not obj.prix_demi_journee:
            obj.prix_demi_journee = 0
        obj.save()
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

# ── Gestion du Personnel (RH) ──────────────────────────────────────────────

from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

GROUPES_METIER = [
    ('Directeur Général',    '👑 Direction'),
    ('Manager Général(e)',   '👑 Direction'),
    ('Responsable Hôtel',    '🏨 Hôtel'),
    ('Réceptionniste',       '🏨 Hôtel'),
    ('Responsable Caisse',   '💰 Caisse'),
    ('Caissier(e)',          '💰 Caisse'),
    ('Manager Cuisine',      '🍽️ Cuisine'),
    ('Cuisinier(e)',         '🍽️ Cuisine'),
    ('Serveuse/Serveur',     '🍽️ Restaurant'),
    ('Agent de Sécurité',    '🔒 Sécurité'),
]


@require_manager
def personnel_list(request):
    utilisateurs = User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name')
    groupes = Group.objects.filter(name__in=[g[0] for g in GROUPES_METIER]).order_by('name')
    context = {
        'utilisateurs': utilisateurs,
        'groupes': groupes,
        'groupes_metier': GROUPES_METIER,
    }
    return render(request, 'parametres/personnel_list.html', context)


@require_manager
def personnel_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type and 'application/json' in request.content_type else request.POST.dict()
            
            username   = data.get('username', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name  = data.get('last_name', '').strip()
            email      = data.get('email', '').strip()
            password   = data.get('password', '').strip()
            groupe_nom = data.get('groupe', '')

            if not username or not password:
                return JsonResponse({'success': False, 'error': 'Username et mot de passe requis'})

            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': f"L'identifiant '{username}' existe déjà"})

            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
            )

            if groupe_nom:
                try:
                    groupe = Group.objects.get(name=groupe_nom)
                    user.groups.add(groupe)
                except Group.DoesNotExist:
                    pass

            return JsonResponse({
                'success': True,
                'message': f'{first_name} {last_name} créé avec succès',
                'user_id': user.pk,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST requis'})


@require_manager
def personnel_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type and 'application/json' in request.content_type else request.POST.dict()
            
            user.first_name = data.get('first_name', user.first_name).strip()
            user.last_name  = data.get('last_name', user.last_name).strip()
            user.email      = data.get('email', user.email).strip()
            user.save()

            # Mettre à jour le groupe
            groupe_nom = data.get('groupe', '')
            if groupe_nom:
                user.groups.clear()
                try:
                    groupe = Group.objects.get(name=groupe_nom)
                    user.groups.add(groupe)
                except Group.DoesNotExist:
                    pass

            return JsonResponse({'success': True, 'message': f'{user.get_full_name()} mis à jour'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST requis'})


@require_manager
def personnel_toggle(request, pk):
    """Activer / Désactiver un utilisateur."""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Impossible de désactiver le superadmin'})
    user.is_active = not user.is_active
    user.save()
    statut = 'activé' if user.is_active else 'désactivé'
    return JsonResponse({'success': True, 'message': f'{user.get_full_name()} {statut}', 'is_active': user.is_active})


@require_manager
def personnel_reset_password(request, pk):
    """Réinitialiser le mot de passe d'un utilisateur."""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_password = data.get('password', '').strip()
            if len(new_password) < 4:
                return JsonResponse({'success': False, 'error': 'Mot de passe trop court (minimum 4 caractères)'})
            user.set_password(new_password)
            user.save()
            return JsonResponse({'success': True, 'message': f'Mot de passe de {user.get_full_name()} réinitialisé'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'POST requis'})


# ═══════════════════════════════════════════════════════════════════════════════
# FORFAITS
# ═══════════════════════════════════════════════════════════════════════════════
from restaurant.models import Forfait, LigneForfait
from cuisine.models import Plat
from bar.models import BoissonBar as BoissonBarModel

@login_required
def forfait_list(request):
    forfaits = Forfait.objects.prefetch_related('lignes__plat', 'lignes__boisson').all()
    return render(request, 'parametres/forfait_list.html', {'forfaits': forfaits})

@login_required
def forfait_create(request):
    plats    = Plat.objects.filter(statut='disponible').order_by('nom')
    boissons = BoissonBarModel.objects.filter(disponible=True).order_by('nom')
    modules  = Forfait.MODULE_CHOICES
    if request.method == 'POST':
        f = Forfait.objects.create(
            nom=request.POST['nom'],
            module=request.POST['module'],
            prix=request.POST['prix'],
            description=request.POST.get('description', ''),
            disponible=request.POST.get('disponible') == 'on',
        )
        if request.FILES.get('image'):
            f.image = request.FILES['image']
            f.save()
        _save_lignes_forfait(request, f)
        messages.success(request, f"Forfait « {f.nom} » créé avec succès.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_form.html', {
        'plats': plats, 'boissons': boissons, 'modules': modules, 'mode': 'create'
    })

@login_required
def forfait_edit(request, pk):
    forfait  = get_object_or_404(Forfait, pk=pk)
    plats    = Plat.objects.filter(statut='disponible').order_by('nom')
    boissons = BoissonBarModel.objects.filter(disponible=True).order_by('nom')
    modules  = Forfait.MODULE_CHOICES
    if request.method == 'POST':
        forfait.nom         = request.POST['nom']
        forfait.module      = request.POST['module']
        forfait.prix        = request.POST['prix']
        forfait.description = request.POST.get('description', '')
        forfait.disponible  = request.POST.get('disponible') == 'on'
        if request.FILES.get('image'):
            forfait.image = request.FILES['image']
        forfait.save()
        forfait.lignes.all().delete()
        _save_lignes_forfait(request, forfait)
        messages.success(request, f"Forfait « {forfait.nom} » modifié.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_form.html', {
        'forfait': forfait, 'plats': plats, 'boissons': boissons,
        'modules': modules, 'mode': 'edit'
    })

@login_required
def forfait_delete(request, pk):
    forfait = get_object_or_404(Forfait, pk=pk)
    if request.method == 'POST':
        forfait.delete()
        messages.success(request, "Forfait supprimé.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_confirm_delete.html', {'forfait': forfait})

def _save_lignes_forfait(request, forfait):
    """Lire les lignes du formulaire dynamique et les enregistrer."""
    types     = request.POST.getlist('ligne_type')
    plat_ids  = request.POST.getlist('ligne_plat')
    bois_ids  = request.POST.getlist('ligne_boisson')
    libelles  = request.POST.getlist('ligne_libelle')
    quantites = request.POST.getlist('ligne_quantite')
    for i, typ in enumerate(types):
        qte = int(quantites[i]) if i < len(quantites) and quantites[i] else 1
        ligne = LigneForfait(forfait=forfait, type_item=typ, quantite=qte, ordre=i)
        if typ == 'plat' and i < len(plat_ids) and plat_ids[i]:
            ligne.plat_id = plat_ids[i]
        elif typ == 'boisson' and i < len(bois_ids) and bois_ids[i]:
            ligne.boisson_id = bois_ids[i]
        elif typ == 'autre' and i < len(libelles) and libelles[i]:
            ligne.libelle = libelles[i]
        ligne.save()
