# cuisine/views_reception.py

import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.db.models import Q
from .models import BonReception, LigneBonReception, Fournisseur, Ingredient, MouvementStock

@login_required
def bon_reception_list(request):
    """Affiche la liste de tous les bons de réception, avec recherche."""
    bons_qs = BonReception.objects.select_related('fournisseur', 'operateur').all().order_by('-date_reception')
    
    query = request.GET.get('q')
    if query:
        bons_qs = bons_qs.filter(
            Q(id__icontains=query) |
            Q(numero_document__icontains=query) |
            Q(fournisseur__nom__icontains=query)
        ).distinct()

    context = {
        'bons': bons_qs,
        'page_title': 'Réceptions'
    }
    return render(request, 'cuisine/bon_reception_list.html', context)

@login_required
def bon_reception_create(request):
    """ Gère la création complète d'un bon de réception sur une seule page. """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Récupérer les données de l'en-tête
                fournisseur_id = request.POST.get('fournisseur')
                numero_document = request.POST.get('numero_document')
                date_reception = request.POST.get('date_reception')

                # 2. Récupérer et parser les lignes d'articles depuis le JSON
                lignes_json = request.POST.get('lignes_reception')
                if not lignes_json:
                    raise ValueError("Aucun article n'a été ajouté au bon.")
                
                try:
                    lignes_data = json.loads(lignes_json)
                    if not lignes_data:
                        messages.error(request, "Vous devez ajouter au moins un article au bon de réception.")
                        return redirect('cuisine:bon_reception_create')
                except json.JSONDecodeError:
                    messages.error(request, "Une erreur technique est survenue (données de lignes invalides).")
                    return redirect('cuisine:bon_reception_create')
                if not lignes_data:
                    raise ValueError("La liste d'articles est vide.")

                # 3. Créer le Bon de Réception principal
                bon = BonReception.objects.create(
                    fournisseur_id=fournisseur_id if fournisseur_id else None,
                    numero_document=numero_document,
                    date_reception=date_reception,
                    operateur=request.user,
                    etat='valide', # On le valide directement
                    date_validation=timezone.now()
                )

                # 4. Créer les Lignes et les Mouvements de Stock
                for ligne_data in lignes_data:
                    article = get_object_or_404(Ingredient, pk=int(ligne_data['article_id']))
                    quantite = Decimal(ligne_data['quantite'])
                    prix_achat = Decimal(ligne_data['prix_achat'])

                    LigneBonReception.objects.create(
                        bon_reception=bon,
                        ingredient=article,
                        quantite=quantite,
                        prix_achat_unitaire=prix_achat
                    )
                    
                    # Améliorer le commentaire pour inclure le numéro de document du fournisseur
                    commentaire = f"Réception via BR n°{bon.id}"
                    if bon.numero_document:
                        commentaire += f" (Doc: {bon.numero_document})"

                    MouvementStock.objects.create(
                        ingredient=article,
                        quantite=quantite,
                        type_mouvement='entree',
                        prix_unitaire=prix_achat,
                        commentaire=commentaire,
                        fournisseur=bon.fournisseur,
                        utilisateur=request.user
                    )

                    # Mise à jour du prix de vente de l'article
                    article.prix_vente = prix_achat
                    article.save()
                
                messages.success(request, f"Bon de réception n°{bon.id} a été créé et validé. Le stock a été mis à jour.")
                return redirect(reverse('cuisine:bon_reception_detail', args=[bon.id]))

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création du bon : {e}")
            return redirect('cuisine:bon_reception_create')

    # Pour la requête GET
    fournisseurs = Fournisseur.objects.all().order_by('nom')
    articles = Ingredient.objects.exclude(categorie__nom__in=['Boisson', 'Boissons']).order_by('nom')
    context = {
        'fournisseurs': fournisseurs,
        'articles': articles,
        'page_title': 'Nouvelle Réception de Stock'
    }
    return render(request, 'cuisine/bon_reception_form.html', context)


@login_required
def bon_reception_detail(request, pk):
    """Affiche les détails d'un bon. La modification n'est plus gérée ici."""
    bon = get_object_or_404(BonReception.objects.prefetch_related('lignes__ingredient'), pk=pk)

    # Logique de validation legacy (devrait être retirée à terme)
    if request.method == 'POST' and 'valider_bon_legacy' in request.POST:
        if bon.etat == 'en_cours':
            try:
                with transaction.atomic():
                    for ligne in bon.lignes.all():
                        MouvementStock.objects.create(
                            ingredient=ligne.ingredient,
                            quantite=ligne.quantite,
                            type_mouvement='entree',
                            prix_unitaire=ligne.prix_achat_unitaire,
                            commentaire=f"Réception via BR n°{bon.id}"
                        )
                    bon.etat = 'valide'
                    bon.date_validation = timezone.now()
                    bon.save()
                    messages.success(request, "Bon validé avec succès.")
                return redirect(reverse('cuisine:bon_reception_detail', args=[pk]))
            except Exception as e:
                messages.error(request, f"Erreur lors de la validation : {e}")

    context = {
        'bon': bon,
        'page_title': f'Détail du Bon de Réception n°{bon.id}'
    }
    return render(request, 'cuisine/bon_reception_detail.html', context)


@login_required
def bon_reception_print(request, pk):
    """Génère une vue imprimable d'un bon de réception."""
    bon = get_object_or_404(BonReception.objects.prefetch_related('lignes__ingredient'), pk=pk)
    context = {
        'bon': bon,
    }
    return render(request, 'cuisine/bon_reception_print.html', context)
