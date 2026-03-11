from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Ingredient, MouvementStock, Fournisseur

@login_required
def mouvement_stock(request):
    """Enregistrer un mouvement de stock (Entrée/Sortie)"""
    articles = Ingredient.objects.select_related('categorie').exclude(categorie__nom__in=['Boisson', 'Boissons']).order_by('nom')
    fournisseurs = Fournisseur.objects.all().order_by('nom')
    
    if request.method == 'POST':
        article_id = request.POST.get('article')
        type_mouv = request.POST.get('type_mouvement')
        quantite = request.POST.get('quantite')
        prix = request.POST.get('prix_unitaire')
        prix_vente = request.POST.get('prix_vente') # Nouveau champ
        commentaire = request.POST.get('commentaire')
        fournisseur_id = request.POST.get('fournisseur')
        
        if article_id and type_mouv and quantite:
            article = get_object_or_404(Ingredient, id=article_id)
            
            fournisseur_instance = None
            if type_mouv == 'entree' and fournisseur_id:
                fournisseur_instance = get_object_or_404(Fournisseur, id=fournisseur_id)

            with transaction.atomic():
                MouvementStock.objects.create(
                    ingredient=article,
                    type_mouvement=type_mouv,
                    quantite=Decimal(quantite),
                    prix_unitaire=Decimal(prix) if prix else None,
                    commentaire=commentaire,
                    utilisateur=request.user,
                    fournisseur=fournisseur_instance
                )
                
                # Mise à jour du prix de vente de l'article si fourni
                if type_mouv == 'entree' and prix_vente:
                    article.prix_vente = Decimal(prix_vente)
                    article.save()
                
            messages.success(request, "Mouvement de stock enregistré.")
            return redirect('cuisine:index')
            
    return render(request, 'cuisine/mouvement_form.html', {
        'articles': articles,
        'fournisseurs': fournisseurs
    })


@login_required
def etat_stock(request):
    """Affiche l'état du stock à une date donnée, avec filtre par catégorie."""
    from datetime import datetime, time
    from .models import CategorieIngredient

    # Le contexte initial pour le formulaire
    context = {
        'categories': CategorieIngredient.objects.all(),
        'date_str': request.GET.get('date', timezone.now().strftime('%Y-%m-%d')),
        'categorie_ids': [int(cid) for cid in request.GET.getlist('categorie') if cid.isdigit()],
    }

    # Si le formulaire n'est pas soumis, on l'affiche
    if 'submit_report' not in request.GET:
        return render(request, 'cuisine/etat_stock_form.html', context)

    # --- Si le formulaire est soumis, on calcule le rapport --- 
    date_str = request.GET.get('date')
    categorie_ids = request.GET.getlist('categorie')

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        target_date = datetime.combine(date_obj, time.max).replace(tzinfo=timezone.get_current_timezone())
    except (ValueError, TypeError):
        target_date = timezone.now()

    ingredients_qs = Ingredient.objects.select_related('categorie', 'unite').all()
    if categorie_ids:
        ingredients_qs = ingredients_qs.filter(categorie_id__in=categorie_ids)
    
    stock_data = []
    total_valeur_cmup = Decimal('0.0')
    total_valeur_vente = Decimal('0.0')

    for ing in ingredients_qs.order_by('nom'):
        stock_at_date = ing.quantite_stock
        mouvements_apres = MouvementStock.objects.filter(
            ingredient=ing,
            date__gt=target_date
        )
        for mvt in mouvements_apres:
            stock_at_date -= mvt.quantite

        valeur_cmup = stock_at_date * ing.prix_moyen
        valeur_vente = stock_at_date * ing.prix_vente
        marge = valeur_vente - valeur_cmup

        total_valeur_cmup += valeur_cmup
        total_valeur_vente += valeur_vente
        
        stock_data.append({
            'ingredient': ing,
            'quantite': stock_at_date,
            'valeur_cmup': valeur_cmup,
            'valeur_vente': valeur_vente,
            'marge': marge,
        })

    total_marge = total_valeur_vente - total_valeur_cmup

    # On ajoute les données calculées au contexte
    context.update({
        'stock_data': stock_data,
        'target_date': target_date,
        'total_valeur_cmup': total_valeur_cmup,
        'total_valeur_vente': total_valeur_vente,
        'total_marge': total_marge,
    })
    
    return render(request, 'cuisine/report_stock.html', context) # Un nouveau template pour le formulaire

@login_required
def inventaire_saisie(request):
    """Saisie d'inventaire physique"""
    if request.method == 'POST':
        date_inventaire = request.POST.get('date_inventaire')
        
        with transaction.atomic():
            count = 0
            for key, value in request.POST.items():
                if key.startswith('stock_physique_'):
                    ing_id = key.split('_')[2]
                    try:
                        physique = Decimal(value)
                        ing = Ingredient.objects.get(id=ing_id)
                        
                        # Calcul de la différence
                        theorique = ing.quantite_stock
                        diff = physique - theorique
                        
                        if diff != 0:
                            # Création du mouvement d'ajustement
                            # Si diff > 0 (Physique > Theorique) => Entrée (Inventaire +)
                            # Si diff < 0 (Physique < Theorique) => Sortie (Inventaire -)
                            
                            # Note: MouvementStock.save() ajoute la quantité au stock
                            # Donc si diff est négatif, ça soustraira correctement
                            
                            MouvementStock.objects.create(
                                ingredient=ing,
                                type_mouvement='inventaire',
                                quantite=diff,
                                commentaire=f"Inventaire du {date_inventaire}",
                                utilisateur=request.user
                            )
                            count += 1
                    except (ValueError, Ingredient.DoesNotExist):
                        continue
                        
            messages.success(request, f"Inventaire enregistré. {count} ajustements effectués.")
            return redirect('cuisine:etat_stock')
            
    ingredients = Ingredient.objects.select_related('categorie').exclude(categorie__nom__in=['Boisson', 'Boissons']).order_by('categorie__nom', 'nom')
    return render(request, 'cuisine/inventaire_saisie.html', {
        'ingredients': ingredients,
        'today': timezone.now().strftime('%Y-%m-%d')
    })
