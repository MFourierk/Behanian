from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
from django.db import transaction
from django.http import JsonResponse
from .models import Ingredient, FicheTechnique, LigneFicheTechnique, MouvementStock, CategorieIngredient, Fournisseur
from restaurant.models import PlatMenu, CategorieMenu
from .forms import ArticleForm, FournisseurForm, CategorieArticleForm, RecetteForm, DetailFicheTechniqueFormSet, RecetteModalForm
from django.utils import timezone
from decimal import Decimal
from .views_stock import etat_stock, inventaire_saisie, mouvement_stock
from .views_reports import rapport_consommation, rapport_pertes, chart_data_mouvements, chart_data_top_consommation, rapports_dashboard
from .views_reception import bon_reception_list, bon_reception_create, bon_reception_detail, bon_reception_print

@login_required
def recette_create_modal(request):
    if request.method == 'POST':
        form = RecetteModalForm(request.POST, request.FILES)
        formset = DetailFicheTechniqueFormSet(request.POST, prefix='formset-new')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    plat, created = PlatMenu.objects.get_or_create(
                        nom=form.cleaned_data['nom'],
                        defaults={
                            'categorie': form.cleaned_data['categorie'],
                            'description': form.cleaned_data['description'],
                            'temps_preparation': form.cleaned_data['temps_preparation'] + form.cleaned_data['temps_cuisson'],
                        }
                    )

                    if not created and hasattr(plat, 'fiche_technique'):
                        return JsonResponse({'success': False, 'errors': {'__all__': ['Un plat avec ce nom a déjà une fiche technique.']}})

                    # Mettre à jour les champs du plat, qu'il soit nouveau ou non
                    plat.categorie = form.cleaned_data['categorie']
                    plat.description = form.cleaned_data['description']
                    plat.temps_preparation = form.cleaned_data['temps_preparation'] + form.cleaned_data['temps_cuisson']
                    plat.disponible = True

                    # Création de la fiche et de ses lignes
                    fiche = FicheTechnique.objects.create(
                        plat=plat,
                        nombre_portions=form.cleaned_data['nombre_portions'],
                        temps_preparation=form.cleaned_data['temps_preparation'],
                        temps_cuisson=form.cleaned_data['temps_cuisson'],
                        instructions=form.cleaned_data['instructions'],
                        image=form.cleaned_data.get('image')
                    )

                    formset.instance = fiche
                    formset.save()

                    # 3. Mettre à jour le prix du plat en fonction des lignes
                    total_prix_vente = Decimal('0.0')
                    for ligne in fiche.lignes.all():
                        quantite = ligne.quantite or Decimal('0.0')
                        prix_unitaire = ligne.prix_vente if ligne.prix_vente is not None else (ligne.ingredient.prix_vente or Decimal('0.0'))
                        total_prix_vente += quantite * prix_unitaire
                    
                    plat.prix = total_prix_vente
                    plat.save()

                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'__all__': [f'Une erreur technique est survenue: {e}']}})
        else:
            errors = {}
            
            # Handle non-field errors from both form and formset
            general_errors = []
            if form.non_field_errors():
                general_errors.extend(form.non_field_errors())
            if formset.non_form_errors():
                general_errors.extend(formset.non_form_errors())
            
            if general_errors:
                errors['Erreurs Générales'] = general_errors[0]

            # Handle field-specific errors from the main form
            for field, error_list in form.errors.items():
                if field != '__all__':
                    field_name = form.fields.get(field).label if form.fields.get(field) else field
                    errors[field_name] = error_list[0]
            
            # Handle field-specific errors from the formset
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, error_list in form_errors.items():
                        field_label = formset.form.base_fields.get(field).label if formset.form.base_fields.get(field) else field
                        errors[f'Ligne {i+1} - {field_label}'] = error_list[0]

            return JsonResponse({'success': False, 'errors': errors})
            
    return JsonResponse({'success': False, 'errors': {'__all__': ['Méthode de requête invalide.']}})


@login_required
def index(request):
    """Tableau de bord de la cuisine"""
    # Alertes de stock
    articles_en_alerte = Ingredient.objects.filter(quantite_stock__lte=F('seuil_alerte'))
    
    # Derniers mouvements
    derniers_mouvements = MouvementStock.objects.select_related('ingredient', 'utilisateur').order_by('-date')[:10]
    
    # Statistiques globales
    total_articles = Ingredient.objects.count()
    valeur_stock_agg = Ingredient.objects.aggregate(valeur=Sum(F('quantite_stock') * F('prix_moyen')))
    valeur_stock = valeur_stock_agg['valeur'] or Decimal('0.00')
    
    context = {
        'articles_en_alerte': articles_en_alerte,
        'derniers_mouvements': derniers_mouvements,
        'total_articles': total_articles,
        'valeur_stock': valeur_stock,
    }
    return render(request, 'cuisine/index.html', context)

@login_required
def article_list(request):
    """Liste des articles et gestion du stock"""
    articles_queryset = Ingredient.objects.select_related('categorie').exclude(categorie__nom__in=['Boisson', 'Boissons']).order_by('nom')

    # Stats
    total_articles = articles_queryset.count()
    valeur_stock_agg = articles_queryset.aggregate(valeur=Sum(F('quantite_stock') * F('prix_moyen')))
    valeur_stock = valeur_stock_agg['valeur'] or Decimal('0.00')
    stock_bas = articles_queryset.filter(quantite_stock__lte=F('seuil_alerte'), quantite_stock__gt=0).count()
    ruptures = articles_queryset.filter(quantite_stock=0).count()
    
    article_form = ArticleForm(prefix='new')
    edit_form = ArticleForm(prefix='edit') # Formulaire pour l'édition

    context = {
        'articles': articles_queryset,
        'total_articles': total_articles,
        'valeur_stock': valeur_stock,
        'stock_bas': stock_bas,
        'ruptures': ruptures,
        'categories': CategorieIngredient.objects.exclude(nom__in=['Boisson', 'Boissons']),
        'article_form': article_form,
        'edit_form': edit_form, # Ajout du formulaire d'édition au contexte
    }
    return render(request, 'cuisine/article_list.html', context)

@login_required
def article_create_modal(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, prefix='new')
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    return JsonResponse({'success': False, 'errors': 'Invalid request'})

@login_required
def article_edit(request, pk):
    article = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article, prefix='edit')
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    
    # Si GET, on renvoie les données de l'article pour pré-remplir le form
    data = {
        'nom': article.nom,
        'code': article.code,
        'categorie': article.categorie.id if article.categorie else '',
        'unite': article.unite.id if article.unite else '',
        'quantite_stock': article.quantite_stock,
        'seuil_alerte': article.seuil_alerte,
        'prix_moyen': article.prix_moyen,
        'prix_vente': article.prix_vente,
        'emplacement': article.emplacement.id if article.emplacement else '',
    }
    return JsonResponse({'success': True, 'data': data})

@login_required
def get_ingredient_details(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, pk=ingredient_id)
    data = {
        'prix_vente': ingredient.prix_vente,
        'prix_moyen': ingredient.prix_moyen
    }
    return JsonResponse(data)

@login_required
def get_ingredients_details(request):
    ingredient_ids = request.GET.getlist('ids[]')
    ingredients = Ingredient.objects.filter(pk__in=ingredient_ids)
    data = {
        'ingredients': {
            ingredient.id: {
                'prix_vente': ingredient.prix_vente,
                'prix_moyen': ingredient.prix_moyen
            } for ingredient in ingredients
        }
    }
    return JsonResponse(data)

@login_required
def fournisseur_list(request):
    """Gérer les fournisseurs"""
    fournisseurs = Fournisseur.objects.all().order_by('nom')
    form = FournisseurForm()
    
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Fournisseur '{form.cleaned_data['nom']}' ajouté.")
            return redirect('cuisine:fournisseur_list')

    return render(request, 'cuisine/fournisseur_list.html', {'fournisseurs': fournisseurs, 'form': form})



@login_required
def transformation_stock(request):
    """Transformer un article en un autre (Ex: Poulet Entier -> 2 Demi Poulets)"""
    if request.method == 'POST':
        source_id = request.POST.get('source_id')
        target_id = request.POST.get('target_id')
        qty_source = request.POST.get('qty_source')
        qty_target = request.POST.get('qty_target')
        
        if source_id and target_id and qty_source and qty_target:
            try:
                with transaction.atomic():
                    source = get_object_or_404(Ingredient, id=source_id)
                    target = get_object_or_404(Ingredient, id=target_id)
                    
                    q_src = Decimal(qty_source)
                    q_tgt = Decimal(qty_target)
                    
                    if source.quantite_stock < q_src:
                        messages.error(request, f"Stock insuffisant pour {source.nom}")
                        return redirect('cuisine:article_list')
                    
                    # 1. Sortie du produit source
                    MouvementStock.objects.create(
                        ingredient=source,
                        type_mouvement='sortie',
                        quantite=q_src,
                        commentaire=f"Transformation vers {target.nom}",
                        utilisateur=request.user
                    )
                    
                    # 2. Entrée du produit cible
                    MouvementStock.objects.create(
                        ingredient=target,
                        type_mouvement='entree',
                        quantite=q_tgt,
                        commentaire=f"Transformation depuis {source.nom}",
                        utilisateur=request.user
                    )
                    
                    messages.success(request, f"Transformation effectuée : {q_src} {source.nom} -> {q_tgt} {target.nom}")
                    
            except Exception as e:
                messages.error(request, f"Erreur lors de la transformation: {str(e)}")
        
    return redirect('cuisine:article_list')

import json

@login_required
def recette_list(request):
    """Liste des fiches techniques avec recherche et filtre."""
    fiches_qs = FicheTechnique.objects.select_related('plat__categorie').all().order_by('plat__nom')

    query = request.GET.get('q')
    if query:
        fiches_qs = fiches_qs.filter(plat__nom__icontains=query)

    categorie_id = request.GET.get('categorie')
    if categorie_id:
        fiches_qs = fiches_qs.filter(plat__categorie_id=categorie_id)

    categories_menu = CategorieMenu.objects.all().order_by('nom')

    # Données des ingrédients pour le calcul JS
    ingredients_data_qs = Ingredient.objects.all()
    ingredients_data = {ing.id: {'prix_moyen': str(ing.prix_moyen or 0), 'prix_vente': str(ing.prix_vente or 0)} for ing in ingredients_data_qs}

    form = RecetteModalForm()
    formset = DetailFicheTechniqueFormSet(prefix='formset-new')

    context = {
        'fiches': fiches_qs,
        'categories_menu': categories_menu,
        'form': form,
        'formset': formset,
        'ingredients_data_json': json.dumps(ingredients_data), 
    }
    return render(request, 'cuisine/recette_list.html', context)

@login_required
def recette_create(request, plat_id=None):
    plat = None
    if plat_id:
        plat = get_object_or_404(PlatMenu, pk=plat_id)

    if request.method == 'POST':
        form = RecetteForm(request.POST, initial={'plat': plat})
        if form.is_valid():
            fiche = form.save()
            messages.success(request, f"La fiche technique pour '{fiche.plat.nom}' a été créée. Ajoutez maintenant les articles.")
            return redirect('cuisine:recette_edit', pk=fiche.pk)
    else:
        form = RecetteForm(initial={'plat': plat})
        if plat:
            form.fields['plat'].disabled = True

    context = {
        'form': form,
        'page_title': 'Nouvelle Fiche Technique'
    }
    return render(request, 'cuisine/recette_form.html', context)



@login_required
def recette_edit(request, pk):
    fiche = get_object_or_404(FicheTechnique, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = RecetteForm(request.POST, request.FILES, instance=fiche)
        formset = DetailFicheTechniqueFormSet(request.POST, instance=fiche, prefix='lignes')

        if form.is_valid() and formset.is_valid():
            nom_plat = request.POST.get('nom_plat')
            if nom_plat and fiche.plat.nom != nom_plat:
                # Vérifier si un autre plat avec ce nom n'existe pas déjà
                if PlatMenu.objects.filter(nom__iexact=nom_plat).exclude(pk=fiche.plat.pk).exists():
                    return JsonResponse({
                        'success': False, 
                        'errors': {'__all__': ['Un plat avec ce nom existe déjà.']}
                    }, status=400)
                fiche.plat.nom = nom_plat

            # Mettre à jour la catégorie du plat
            categorie = form.cleaned_data.get('categorie')
            if categorie and fiche.plat.categorie != categorie:
                fiche.plat.categorie = categorie

            fiche.plat.save()

            fiche = form.save()
            formset.save()

            total_prix_vente = Decimal('0.0')
            for ligne in formset.cleaned_data:
                if not ligne.get('DELETE', False):
                    ingredient = ligne.get('ingredient')
                    quantite = ligne.get('quantite')
                    prix_vente_specifique = ligne.get('prix_vente')

                    if ingredient and quantite:
                        prix_unitaire = prix_vente_specifique if prix_vente_specifique is not None else ingredient.prix_vente
                        if prix_unitaire is not None:
                            total_prix_vente += quantite * prix_unitaire
            
            # Mettre à jour le prix du plat et sauvegarder
            if fiche.plat:
                fiche.plat.prix = total_prix_vente
                fiche.plat.save()
            
            
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                messages.success(request, "Fiche technique mise à jour avec succès.")
                return redirect('cuisine:recette_detail', pk=fiche.pk)
        else:
            if is_ajax:
                # Renvoyer les erreurs au format JSON pour les requêtes AJAX
                form_errors = form.errors.as_json()
                formset_errors = formset.errors.as_json()
                return JsonResponse({
                    'success': False, 
                    'errors': {'form': form_errors, 'formset': formset_errors}
                }, status=400)
            # Pour les requêtes non-AJAX, on continue comme avant (la page se recharge avec les erreurs)

    # Si ce n'est pas POST, on affiche simplement le formulaire (pour la page complète, pas la modale)
    form = RecetteForm(instance=fiche)
    formset = DetailFicheTechniqueFormSet(instance=fiche, prefix='lignes')
    
    context = {
        'form': form,
        'formset': formset,
        'fiche': fiche,
        'page_title': f"Modifier Fiche: {fiche.plat.nom}"
    }
    return render(request, 'cuisine/recette_form.html', context)


@login_required
def recette_delete(request, pk):
    """Supprimer une fiche technique et le plat associé."""
    fiche = get_object_or_404(FicheTechnique, pk=pk)
    if request.method == 'POST':
        nom_plat = fiche.plat.nom
        # Supprimer d'abord le plat associé
        fiche.plat.delete()
        # La fiche technique est automatiquement supprimée grâce à on_delete=models.CASCADE
        messages.success(request, f"La fiche technique et le plat '{nom_plat}' ont été supprimés.")
        return redirect('cuisine:recette_list')
    return render(request, 'cuisine/recette_confirm_delete.html', {'object': fiche})

from django.template.loader import render_to_string

@login_required
def recette_edit_get_form(request, pk):
    fiche = get_object_or_404(FicheTechnique.objects.select_related('plat__categorie'), pk=pk)
    
    form = RecetteForm(instance=fiche)
    formset = DetailFicheTechniqueFormSet(instance=fiche, prefix='lignes')
    
    modal_body_html = render_to_string('cuisine/partials/edit_recette_modal_body.html', {
        'form': form,
        'formset': formset,
    }, request=request)

    ingredients_data_qs = Ingredient.objects.all()
    ingredients_data = {ing.id: {'prix_moyen': str(ing.prix_moyen or 0), 'prix_vente': str(ing.prix_vente or 0)} for ing in ingredients_data_qs}

    return JsonResponse({
        'success': True,
        'modal_body': modal_body_html,
        'ingredients_data': ingredients_data
    })

@login_required
def get_plat_details(request, plat_id):
    """API pour récupérer les détails d'un plat pour l'édition (utilisé par l'ancienne interface)"""
    plat = get_object_or_404(PlatMenu, id=plat_id)
    data = {
        'id': plat.id,
        'nom': plat.nom,
        'categorie_id': plat.categorie.id,
        'prix': str(plat.prix),
        'temps_preparation': plat.temps_preparation,
        'description': plat.description,
        'is_accompagnement': plat.is_accompagnement,
    }
    
    if hasattr(plat, 'fiche_technique'):
        fiche = plat.fiche_technique
        data.update({
            'has_fiche': True,
            'portions': fiche.nombre_portions,
            'instructions': fiche.instructions,
            'articles': [
                {
                    'id': ligne.ingredient.id,
                    'nom': ligne.ingredient.nom,
                    'quantite': str(ligne.quantite),
                    'unite': ligne.ingredient.get_unite_display()
                } for ligne in fiche.lignes.all()
            ]
        })
    else:
        data['has_fiche'] = False
    
    return JsonResponse({'success': True, 'data': data})

