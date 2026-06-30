from utils.permissions import require_module_access, require_manager, require_chambre_access, _is_responsable_hotel
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db.models.expressions import RawSQL

from hotel.models import Chambre
from restaurant.models import Table, PlatMenu, CategorieMenu
from espaces_evenementiels.models import EspaceEvenementiel
from bar.models import BoissonBar, CategorieBar, TableBar

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

@login_required
def parametres_index(request):
    from utils.permissions import user_has_access
    if not (user_has_access(request.user, 'parametres') or request.user.is_superuser):
        messages.error(request, "Accès refusé — réservé aux managers.")
        return redirect('dashboard:index')
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
@method_decorator(require_chambre_access, name='dispatch')
class ChambreListView(ListView):
    model = Chambre
    template_name = 'parametres/chambre_list.html'
    context_object_name = 'chambres'

@method_decorator(require_chambre_access, name='dispatch')
class ChambreCreateView(CreateView):
    model = Chambre
    template_name = 'parametres/chambre_form.html'
    fields = '__all__'
    success_url = reverse_lazy('parametres:chambre_list')

    def form_valid(self, form):
        messages.success(self.request, "Chambre créée avec succès.")
        return super().form_valid(form)

@method_decorator(require_chambre_access, name='dispatch')
class ChambreUpdateView(UpdateView):
    model = Chambre
    template_name = 'parametres/chambre_form.html'
    fields = '__all__'
    success_url = reverse_lazy('parametres:chambre_list')

    def form_valid(self, form):
        messages.success(self.request, "Chambre modifiée avec succès.")
        return super().form_valid(form)

@method_decorator(require_chambre_access, name='dispatch')
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

    def get_queryset(self):
        return Table.objects.annotate(
            num=RawSQL("CAST(REGEXP_REPLACE(numero, '[^0-9]', '', 'g') AS INTEGER)", [])
        ).order_by('num', 'numero')

@method_decorator(login_required, name='dispatch')
class TableCreateView(CreateView):
    model = Table
    template_name = 'parametres/table_form.html'
    fields = ['numero', 'capacite', 'statut']
    success_url = reverse_lazy('parametres:table_list')

    def form_valid(self, form):
        messages.success(self.request, "Table créée avec succès.")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TableUpdateView(UpdateView):
    model = Table
    template_name = 'parametres/table_form.html'
    fields = ['numero', 'capacite', 'statut']
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
    ('Manager Hôtel',        '🏨 Hôtel'),
    ('Responsable Hôtel',    '🏨 Hôtel'),
    ('Réceptionniste',       '🏨 Hôtel'),
    ('Chef caissier(e)',      '💰 Caisse'),
    ('Caissier(e)',          '💰 Caisse'),
    ('Manager Cuisine',      '🍽️ Cuisine'),
    ('Cuisinier(e)',         '🍽️ Cuisine'),
    ('Serveuse/Serveur',     '🍽️ Restaurant'),
    ('Responsable Cave',     '🍷 Cave'),
    ('Agent de Sécurité',    '🔒 Sécurité'),
]

# Groupes sans accès à l'application — pas de connexion possible, mot de passe inutile
GROUPES_SANS_ACCES = frozenset([
    'Serveuse/Serveur',
    'Agent de Sécurité',
    'Cuisinier(e)',
    'Utilisateur Simple',
])


@require_manager
def personnel_list(request):
    utilisateurs = User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name')
    noms_systeme = {g[0] for g in GROUPES_METIER}
    groupes = Group.objects.filter(name__in=noms_systeme).order_by('name')
    groupes_custom = Group.objects.exclude(name__in=noms_systeme).order_by('name')
    context = {
        'utilisateurs': utilisateurs,
        'groupes': groupes,
        'groupes_custom': groupes_custom,
        'groupes_metier': GROUPES_METIER,
        'noms_systeme': noms_systeme,
        'groupes_sans_acces': GROUPES_SANS_ACCES,
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

            if not username:
                return JsonResponse({'success': False, 'error': 'Identifiant requis'})

            # Le mot de passe n'est requis que pour les comptes avec accès à l'application.
            # Les groupes terrain (serveurs, agents, cuisiniers…) et les groupes personnalisés
            # n'ont pas accès à l'interface — leur compte reçoit un mot de passe inutilisable.
            noms_systeme = {g[0] for g in GROUPES_METIER}
            sans_acces = groupe_nom in GROUPES_SANS_ACCES or groupe_nom not in noms_systeme

            if not sans_acces and not password:
                return JsonResponse({'success': False, 'error': 'Mot de passe requis pour ce type de compte'})
            if password and len(password) < 4:
                return JsonResponse({'success': False, 'error': 'Mot de passe trop court (minimum 4 caractères)'})

            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': f"L'identifiant '{username}' existe déjà"})

            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password if password else None,
            )

            if groupe_nom:
                groupe, _ = Group.objects.get_or_create(name=groupe_nom)
                user.groups.add(groupe)

            return JsonResponse({
                'success': True,
                'message': f'{(first_name + " " + last_name).strip() or username} créé avec succès',
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
            
            new_username = data.get('username', '').strip()
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    return JsonResponse({'success': False, 'error': f"L'identifiant '{new_username}' est déjà utilisé"})
                user.username = new_username
            user.first_name = data.get('first_name', user.first_name).strip()
            user.last_name  = data.get('last_name', user.last_name).strip()
            user.email      = data.get('email', user.email).strip()
            user.save()

            # Mettre à jour le groupe
            groupe_nom = data.get('groupe', '')
            if groupe_nom:
                user.groups.clear()
                groupe, _ = Group.objects.get_or_create(name=groupe_nom)
                user.groups.add(groupe)

            return JsonResponse({'success': True, 'message': f'{user.get_full_name()} mis à jour'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST requis'})


@require_manager
@require_POST
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
@require_POST
def personnel_delete(request, pk):
    """Supprimer un utilisateur (interdit pour superadmin et soi-même)."""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Impossible de supprimer le Super Administrateur'})
    if user == request.user:
        return JsonResponse({'success': False, 'error': 'Impossible de supprimer votre propre compte'})
    nom = user.get_full_name() or user.username
    user.delete()
    return JsonResponse({'success': True, 'message': f'{nom} supprimé définitivement'})


@require_manager
@require_POST
def groupe_create(request):
    """Crée un groupe terrain personnalisé (sans accès à l'application)."""
    nom = request.POST.get('nom', '').strip()
    noms_systeme = {g[0] for g in GROUPES_METIER}
    if not nom:
        messages.error(request, "Le nom du poste est requis.")
    elif nom in noms_systeme:
        messages.error(request, f"« {nom} » est un poste système — utilisez « Initialiser les postes ».")
    else:
        _, created = Group.objects.get_or_create(name=nom)
        if created:
            messages.success(request, f"Poste « {nom} » créé. Il n'aura aucun accès à l'application.")
        else:
            messages.info(request, f"Le poste « {nom} » existe déjà.")
    return redirect('parametres:personnel_list')


@require_manager
@require_POST
def groupe_delete(request, pk):
    """Supprime un groupe terrain personnalisé (protège les groupes système)."""
    groupe = get_object_or_404(Group, pk=pk)
    noms_systeme = {g[0] for g in GROUPES_METIER}
    if groupe.name in noms_systeme:
        messages.error(request, f"« {groupe.name} » est un poste système et ne peut pas être supprimé.")
        return redirect('parametres:personnel_list')
    if groupe.user_set.exists():
        messages.error(request, f"Impossible de supprimer « {groupe.name} » : {groupe.user_set.count()} membre(s) y sont rattachés.")
        return redirect('parametres:personnel_list')
    nom = groupe.name
    groupe.delete()
    messages.success(request, f"Poste « {nom} » supprimé.")
    return redirect('parametres:personnel_list')


@require_manager
@require_POST
def initialiser_groupes(request):
    """Crée tous les groupes métier définis dans GROUPES_METIER s'ils n'existent pas."""
    crees = []
    for nom, _ in GROUPES_METIER:
        _, created = Group.objects.get_or_create(name=nom)
        if created:
            crees.append(nom)
    if crees:
        messages.success(request, f"{len(crees)} groupe(s) créé(s) : {', '.join(crees)}")
    else:
        messages.info(request, "Tous les groupes métier existent déjà.")
    return redirect('parametres:personnel_list')


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


@require_manager
def forfait_list(request):
    module_filter = request.GET.get('module', '')
    forfaits = Forfait.objects.prefetch_related('lignes__plat', 'lignes__boisson').all()
    if module_filter:
        forfaits = forfaits.filter(module=module_filter)
    from restaurant.models import SouscriptionForfait
    nb_actifs        = Forfait.objects.filter(disponible=True).count()
    nb_souscriptions = SouscriptionForfait.objects.count()
    nb_modules       = Forfait.objects.values('module').distinct().count()
    return render(request, 'parametres/forfait_list.html', {
        'forfaits':         forfaits,
        'module_filter':    module_filter,
        'modules':          Forfait.MODULE_CHOICES,
        'nb_actifs':        nb_actifs,
        'nb_souscriptions': nb_souscriptions,
        'nb_modules':       nb_modules,
    })


@require_manager
def forfait_create(request):
    plats    = Plat.objects.filter(statut='disponible').order_by('nom')
    boissons = BoissonBarModel.objects.filter(disponible=True).order_by('nom')
    modules  = Forfait.MODULE_CHOICES
    if request.method == 'POST':
        f = Forfait.objects.create(
            nom=request.POST['nom'],
            module=request.POST.get('module', 'piscine'),
            prix=request.POST['prix'],
            description=request.POST.get('description', ''),
            disponible=request.POST.get('disponible') == 'on',
        )
        if request.FILES.get('image'):
            f.image = request.FILES['image']
            f.save()
        _save_lignes_forfait(request, f)
        messages.success(request, f"Forfait \u00ab {f.nom} \u00bb cr\u00e9\u00e9 avec succ\u00e8s.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_form.html', {
        'plats': plats, 'boissons': boissons, 'modules': modules, 'mode': 'create'
    })


@require_manager
def forfait_edit(request, pk):
    forfait  = get_object_or_404(Forfait, pk=pk)
    plats    = Plat.objects.filter(statut='disponible').order_by('nom')
    boissons = BoissonBarModel.objects.filter(disponible=True).order_by('nom')
    modules  = Forfait.MODULE_CHOICES
    if request.method == 'POST':
        forfait.nom         = request.POST['nom']
        forfait.module      = request.POST.get('module', forfait.module)
        forfait.prix        = request.POST['prix']
        forfait.description = request.POST.get('description', '')
        forfait.disponible  = request.POST.get('disponible') == 'on'
        if request.FILES.get('image'):
            forfait.image = request.FILES['image']
        forfait.save()
        forfait.lignes.all().delete()
        _save_lignes_forfait(request, forfait)
        messages.success(request, f"Forfait \u00ab {forfait.nom} \u00bb modifi\u00e9.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_form.html', {
        'forfait': forfait, 'plats': plats, 'boissons': boissons,
        'modules': modules, 'mode': 'edit'
    })


@require_manager
def forfait_delete(request, pk):
    forfait = get_object_or_404(Forfait, pk=pk)
    if request.method == 'POST':
        forfait.delete()
        messages.success(request, "Forfait supprim\u00e9.")
        return redirect('parametres:forfait_list')
    return render(request, 'parametres/forfait_confirm_delete.html', {'forfait': forfait})


def _save_lignes_forfait(request, forfait):
    """
    Enregistre les lignes du formulaire simplifié.
    Chaque ligne a : ligne_item (plat:ID | boisson:ID | autre), ligne_libelle, ligne_quantite.
    """
    items     = request.POST.getlist('ligne_item')
    libelles  = request.POST.getlist('ligne_libelle')
    quantites = request.POST.getlist('ligne_quantite')

    ordre = 0
    for i, item in enumerate(items):
        if not item:
            continue
        qte     = max(1, int(quantites[i])) if i < len(quantites) and quantites[i].isdigit() else 1
        libelle = libelles[i].strip() if i < len(libelles) else ''

        ligne = LigneForfait(forfait=forfait, quantite=qte, ordre=ordre)

        if item.startswith('plat:'):
            plat_id = item.split(':', 1)[1]
            if not plat_id:
                continue
            ligne.type_item = 'plat'
            ligne.plat_id   = plat_id
        elif item.startswith('boisson:'):
            bois_id = item.split(':', 1)[1]
            if not bois_id:
                continue
            ligne.type_item  = 'boisson'
            ligne.boisson_id = bois_id
        elif item == 'autre':
            if not libelle:
                continue
            ligne.type_item = 'autre'
            ligne.libelle   = libelle
        else:
            continue

        ligne.save()
        ordre += 1


# ═══════════════════════════════════════════════════════════════════════════════
# SOUSCRIPTIONS FORFAIT
# ═══════════════════════════════════════════════════════════════════════════════
from restaurant.models import SouscriptionForfait
from facturation.models import Client, Ticket
from django.utils import timezone as tz
import json


@require_manager
def souscription_list(request):
    souscriptions = (SouscriptionForfait.objects
                     .select_related('forfait', 'client', 'cree_par', 'ticket')
                     .order_by('-date_souscription'))
    statut_filter = request.GET.get('statut', '')
    module_filter = request.GET.get('module', '')
    if statut_filter:
        souscriptions = souscriptions.filter(statut=statut_filter)
    if module_filter:
        souscriptions = souscriptions.filter(forfait__module=module_filter)
    return render(request, 'parametres/souscription_list.html', {
        'souscriptions':  souscriptions,
        'statut_filter':  statut_filter,
        'module_filter':  module_filter,
        'statut_choices': SouscriptionForfait.STATUT_CHOICES,
        'module_choices': Forfait.MODULE_CHOICES,
    })


@require_manager
def souscription_create(request, forfait_pk):
    forfait = get_object_or_404(Forfait, pk=forfait_pk, disponible=True)
    clients = Client.objects.order_by('nom', 'prenom')

    if request.method == 'POST':
        client_id    = request.POST.get('client_id', '').strip()
        nom_client   = request.POST.get('nom_client', '').strip()
        date_val_str = request.POST.get('date_validite', '').strip()
        mode_paie    = request.POST.get('mode_paiement', 'especes')
        montant_str  = request.POST.get('montant_paye', str(forfait.prix)).strip()
        reference    = request.POST.get('reference', '').strip()
        notes        = request.POST.get('notes', '').strip()

        if not client_id and not nom_client:
            messages.error(request, "Saisissez un client existant ou un nom libre.")
            return render(request, 'parametres/souscription_form.html', {
                'forfait': forfait, 'clients': clients,
                'mode_choices': SouscriptionForfait.MODE_PAIEMENT_CHOICES,
            })

        from decimal import Decimal, InvalidOperation
        try:
            montant = Decimal(montant_str)
        except (InvalidOperation, ValueError):
            montant = forfait.prix

        date_validite = None
        if date_val_str:
            from datetime import date
            try:
                date_validite = date.fromisoformat(date_val_str)
            except ValueError:
                pass

        from datetime import datetime
        num_ticket = f"TKT-FORF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        lignes_txt = '\n'.join(
            f"  {l.quantite}x {l.nom_affiche}"
            for l in forfait.lignes.select_related('plat', 'boisson').all()
        )
        client_obj = Client.objects.filter(pk=client_id).first() if client_id else None
        contenu_ticket = (
            f"FORFAIT : {forfait.nom}\n"
            f"Module  : {forfait.get_module_display()}\n"
            f"Client  : {client_obj or nom_client}\n"
            f"Contenu :\n{lignes_txt or '  (aucun element)'}\n"
            f"Reference : {reference or '--'}"
        )

        ticket = Ticket.objects.create(
            numero=num_ticket,
            module=forfait.module if forfait.module in [m[0] for m in Ticket.MODULE_CHOICES] else 'autre',
            client=client_obj,
            montant_total=montant,
            montant_paye=montant,
            mode_paiement=mode_paie,
            contenu=contenu_ticket,
            cree_par=request.user,
        )

        sous = SouscriptionForfait.objects.create(
            forfait=forfait,
            client=client_obj,
            nom_client=nom_client if not client_obj else '',
            date_validite=date_validite,
            statut='active',
            montant_paye=montant,
            mode_paiement=mode_paie,
            reference=reference,
            notes=notes,
            cree_par=request.user,
            ticket=ticket,
        )

        messages.success(request,
            f"Forfait {forfait.nom!r} lie a {sous.client_display}. Ticket {num_ticket} genere.")
        return redirect('parametres:souscription_list')

    return render(request, 'parametres/souscription_form.html', {
        'forfait':      forfait,
        'clients':      clients,
        'mode_choices': SouscriptionForfait.MODE_PAIEMENT_CHOICES,
    })


@require_manager
@require_POST
def souscription_changer_statut(request, pk):
    sous   = get_object_or_404(SouscriptionForfait, pk=pk)
    statut = request.POST.get('statut', '')
    valides = [s[0] for s in SouscriptionForfait.STATUT_CHOICES]
    if statut not in valides:
        return JsonResponse({'success': False, 'error': 'Statut invalide'})
    sous.statut = statut
    sous.save()
    return JsonResponse({'success': True, 'statut': sous.get_statut_display()})


# ── MOBILE MONEY — Opérateurs ────────────────────────────────

@require_manager
def mobile_money_list(request):
    from parametres.models import OperateurMobileMoney
    operateurs = OperateurMobileMoney.objects.all()
    return render(request, 'parametres/mobile_money_list.html', {'operateurs': operateurs})


@require_manager
def mobile_money_create(request):
    from parametres.models import OperateurMobileMoney
    if request.method == 'POST':
        nom   = request.POST.get('nom', '').strip()
        ordre = int(request.POST.get('ordre', 0) or 0)
        actif = request.POST.get('actif') == 'on'
        if not nom:
            messages.error(request, "Le nom de l'opérateur est obligatoire.")
            return redirect('parametres:mobile_money_create')
        op = OperateurMobileMoney(nom=nom, ordre=ordre, actif=actif)
        if 'image' in request.FILES:
            op.image = request.FILES['image']
        op.save()
        messages.success(request, f"Opérateur « {nom} » ajouté.")
        return redirect('parametres:mobile_money_list')
    return render(request, 'parametres/mobile_money_form.html', {'action': 'Ajouter'})


@require_manager
def mobile_money_update(request, pk):
    from parametres.models import OperateurMobileMoney
    op = get_object_or_404(OperateurMobileMoney, pk=pk)
    if request.method == 'POST':
        op.nom   = request.POST.get('nom', op.nom).strip()
        op.ordre = int(request.POST.get('ordre', op.ordre) or 0)
        op.actif = request.POST.get('actif') == 'on'
        if 'image' in request.FILES:
            op.image = request.FILES['image']
        op.save()
        messages.success(request, f"Opérateur « {op.nom} » mis à jour.")
        return redirect('parametres:mobile_money_list')
    return render(request, 'parametres/mobile_money_form.html', {'action': 'Modifier', 'operateur': op})


@require_manager
def mobile_money_delete(request, pk):
    from parametres.models import OperateurMobileMoney
    op = get_object_or_404(OperateurMobileMoney, pk=pk)
    if request.method == 'POST':
        nom = op.nom
        op.delete()
        messages.success(request, f"Opérateur « {nom} » supprimé.")
        return redirect('parametres:mobile_money_list')
    return render(request, 'parametres/mobile_money_confirm_delete.html', {'operateur': op})


@require_manager
@require_POST
def mobile_money_toggle(request, pk):
    from parametres.models import OperateurMobileMoney
    op = get_object_or_404(OperateurMobileMoney, pk=pk)
    op.actif = not op.actif
    op.save()
    return JsonResponse({'success': True, 'actif': op.actif})
