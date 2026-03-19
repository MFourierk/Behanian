from utils.permissions import require_module_access
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from .models import (
    BonCommandeBar, LigneBonCommandeBar, BoissonBar,
    MouvementStockBar, CategorieBar, UniteVente, Client,
    BonReceptionBar, LigneBonReceptionBar,
    InventaireBar, LigneInventaireBar,
    CasseBar, LigneCasseBar
)
from cuisine.models import Fournisseur


@require_module_access('bar')
def bar_dashboard(request):
    context = {'page_title': 'Tableau de Bord - Cave'}
    return render(request, 'bar/dashboard.html', context)


@require_module_access('bar')
def stock_management(request):
    boissons = BoissonBar.objects.filter(statut='actif')

    total_articles = boissons.count()
    valeur_stock = sum(b.prix * b.quantite_stock for b in boissons)
    stock_bas = boissons.filter(quantite_stock__lte=10, quantite_stock__gt=0).count()
    ruptures = boissons.filter(quantite_stock=0).count()
    commandes_en_cours = BonCommandeBar.objects.filter(statut__in=['brouillon', 'confirme', 'envoye', 'partiel']).count()
    total_unites = boissons.aggregate(total=Sum('quantite_stock'))['total'] or 0

    aucune_rupture = ruptures == 0
    seuils_definis = not boissons.filter(seuil_alerte=0).exists()
    prix_renseignes = not boissons.filter(prix=0).exists()
    categories_definies = not boissons.filter(categorie__isnull=True).exists()

    bonnes_pratiques = [
        {'ok': aucune_rupture, 'titre': 'Aucune rupture de stock', 'detail': 'Tous les articles sont disponibles.' if aucune_rupture else f'{ruptures} article(s) en rupture.'},
        {'ok': seuils_definis, 'titre': 'Seuils minimum définis pour tous les articles', 'detail': "Tous les articles ont un seuil d'alerte configuré." if seuils_definis else "Certains articles n'ont pas de seuil défini."},
        {'ok': prix_renseignes, 'titre': 'Prix de vente renseigné pour tous les articles', 'detail': 'Tous les prix sont renseignés.' if prix_renseignes else "Certains articles n'ont pas de prix."},
        {'ok': categories_definies, 'titre': 'Catégories définies pour tous les articles', 'detail': 'Tous les articles ont une catégorie.' if categories_definies else "Certains articles n'ont pas de catégorie."},
    ]
    score = sum(1 for p in bonnes_pratiques if p['ok'])
    articles_critiques = boissons.filter(Q(quantite_stock=0) | Q(quantite_stock__lte=10)).order_by('quantite_stock')

    # Bons de commande pour l'onglet
    bons = BonCommandeBar.objects.select_related('fournisseur', 'client', 'cree_par').all()
    # Filtres bons de commande
    bc_type = request.GET.get('bc_type', '')
    bc_statut = request.GET.get('bc_statut', '')
    bc_q = request.GET.get('bc_q', '')
    if bc_type:
        bons = bons.filter(type_commande=bc_type)
    if bc_statut:
        bons = bons.filter(statut=bc_statut)
    if bc_q:
        bons = bons.filter(Q(numero__icontains=bc_q) | Q(fournisseur__nom__icontains=bc_q) | Q(client__nom__icontains=bc_q))

    # Stats bons de commande
    bc_total = BonCommandeBar.objects.count()
    bc_brouillons = BonCommandeBar.objects.filter(statut='brouillon').count()
    bc_en_cours = BonCommandeBar.objects.filter(statut__in=['confirme', 'envoye', 'partiel']).count()
    bc_en_retard = sum(1 for b in BonCommandeBar.objects.filter(statut__in=['confirme', 'envoye', 'partiel']) if b.est_en_retard)

    # Mouvements du mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mouvements = MouvementStockBar.objects.select_related('boisson', 'utilisateur').order_by('-date')[:100]
    mv_entrees_mois = MouvementStockBar.objects.filter(type_mouvement='entree', date__gte=debut_mois).count()
    mv_sorties_mois = MouvementStockBar.objects.filter(type_mouvement__in=['sortie', 'prelevement'], date__gte=debut_mois).count()
    mv_casses_mois = MouvementStockBar.objects.filter(type_mouvement='casse', date__gte=debut_mois).count()
    mv_total_mois = MouvementStockBar.objects.filter(date__gte=debut_mois).count()

    # Bons de réception
    br_q = request.GET.get('br_q', '')
    br_statut = request.GET.get('br_statut', '')
    receptions = BonReceptionBar.objects.select_related('fournisseur', 'operateur', 'bon_commande').all()
    if br_q:
        receptions = receptions.filter(Q(numero__icontains=br_q) | Q(fournisseur__nom__icontains=br_q) | Q(numero_document_fournisseur__icontains=br_q))
    if br_statut:
        receptions = receptions.filter(statut=br_statut)

    br_total = BonReceptionBar.objects.count()
    br_valides = BonReceptionBar.objects.filter(statut='valide').count()
    br_en_cours = BonReceptionBar.objects.filter(statut__in=['brouillon', 'en_cours']).count()
    br_avec_ecarts = sum(1 for br in BonReceptionBar.objects.filter(statut='valide') if br.a_des_ecarts)

    context = {
        'page_title': 'Stock',
        'total_articles': total_articles,
        'valeur_stock': valeur_stock,
        'stock_bas': stock_bas,
        'ruptures': ruptures,
        'commandes_en_cours': commandes_en_cours,
        'total_unites': total_unites,
        'bonnes_pratiques': bonnes_pratiques,
        'score': score,
        'score_total': len(bonnes_pratiques),
        'articles_critiques': articles_critiques,
        'boissons': BoissonBar.objects.exclude(statut='supprime'),
        'categories': CategorieBar.objects.all(),
        # Bons de commande
        'bons': bons,
        'bc_total': bc_total,
        'bc_brouillons': bc_brouillons,
        'bc_en_cours': bc_en_cours,
        'bc_en_retard': bc_en_retard,
        'fournisseurs': Fournisseur.objects.all(),
        'clients': Client.objects.filter(actif=True),
        'bc_type': bc_type,
        'bc_statut': bc_statut,
        'bc_q': bc_q,
        # Bons de réception
        'receptions': receptions,
        'br_total': br_total,
        'br_valides': br_valides,
        'br_en_cours': br_en_cours,
        'br_avec_ecarts': br_avec_ecarts,
        'br_q': br_q,
        'br_statut': br_statut,
        # Casses
        'casses': CasseBar.objects.select_related('declare_par').all()[:50],
        'css_total': CasseBar.objects.count(),
        'css_mois': CasseBar.objects.filter(date_casse__gte=timezone.now().replace(day=1).date()).count(),
        'css_valeur_mois': sum(c.total_valeur for c in CasseBar.objects.filter(date_casse__gte=timezone.now().replace(day=1).date(), statut='valide')),
        'css_en_attente': CasseBar.objects.filter(statut='declare').count(),
        # Inventaires
        'inventaires': InventaireBar.objects.select_related('cree_par').all()[:20],
        'inv_total': InventaireBar.objects.count(),
        'inv_en_cours': InventaireBar.objects.filter(statut__in=['brouillon','en_cours']).count(),
        'inv_valides': InventaireBar.objects.filter(statut='valide').count(),
        # Mouvements
        'mouvements': mouvements,
        'mv_entrees_mois': mv_entrees_mois,
        'mv_sorties_mois': mv_sorties_mois,
        'mv_casses_mois': mv_casses_mois,
        'mv_total_mois': mv_total_mois,
    }
    return render(request, 'bar/stock_management.html', context)


# ===== ARTICLES =====

@require_module_access('bar')
def articles_list(request):
    articles = BoissonBar.objects.exclude(statut='supprime')
    categories = CategorieBar.objects.all()
    q = request.GET.get('q', '')
    categorie_id = request.GET.get('categorie', '')
    statut = request.GET.get('statut', '')
    if q:
        articles = articles.filter(Q(nom__icontains=q) | Q(reference__icontains=q))
    if categorie_id:
        articles = articles.filter(categorie_id=categorie_id)
    if statut:
        articles = articles.filter(statut=statut)
    context = {
        'page_title': 'Articles',
        'articles': articles,
        'categories': categories,
        'q': q,
        'categorie_id': categorie_id,
        'statut_filtre': statut,
        'total': articles.count(),
    }
    return render(request, 'bar/articles_list.html', context)


@require_module_access('bar')
def article_create(request):
    categories = CategorieBar.objects.all()
    unites = UniteVente.objects.all()
    if request.method == 'POST':
        article = BoissonBar(
            nom=request.POST.get('nom'),
            reference=request.POST.get('reference') or None,
            categorie_id=request.POST.get('categorie'),
            description=request.POST.get('description', ''),
            mode_prix=request.POST.get('mode_prix', 'manuel'),
            prix_achat=request.POST.get('prix_achat', 0) or 0,
            marge=request.POST.get('marge', 0) or 0,
            prix=request.POST.get('prix', 0) or 0,
            unite_standard=request.POST.get('unite_standard', 'bouteille'),
            unite_personnalisee_id=request.POST.get('unite_personnalisee') or None,
            seuil_alerte=request.POST.get('seuil_alerte', 10) or 10,
            disponible=request.POST.get('disponible') == 'on',
            statut=request.POST.get('statut', 'actif'),
            est_compose=request.POST.get('est_compose') == 'on',
        )
        if request.FILES.get('image'):
            article.image = request.FILES.get('image')
        article.save()
        messages.success(request, f"Article '{article.nom}' créé avec succès.")
        return redirect('bar:stock_management' + '?tab=articles')
    context = {'page_title': 'Nouvel Article', 'categories': categories, 'unites': unites, 'mode': 'create'}
    return render(request, 'bar/article_form.html', context)


@require_module_access('bar')
def article_edit(request, pk):
    article = get_object_or_404(BoissonBar, pk=pk)
    categories = CategorieBar.objects.all()
    unites = UniteVente.objects.all()
    if request.method == 'POST':
        article.nom = request.POST.get('nom')
        article.reference = request.POST.get('reference') or None
        article.categorie_id = request.POST.get('categorie')
        article.description = request.POST.get('description', '')
        article.mode_prix = request.POST.get('mode_prix', 'manuel')
        article.prix_achat = request.POST.get('prix_achat', 0) or 0
        article.marge = request.POST.get('marge', 0) or 0
        article.prix = request.POST.get('prix', 0) or 0
        article.unite_standard = request.POST.get('unite_standard', 'bouteille')
        article.unite_personnalisee_id = request.POST.get('unite_personnalisee') or None
        article.seuil_alerte = request.POST.get('seuil_alerte', 10) or 10
        article.disponible = request.POST.get('disponible') == 'on'
        article.statut = request.POST.get('statut', 'actif')
        article.est_compose = request.POST.get('est_compose') == 'on'
        if request.FILES.get('image'):
            article.image = request.FILES.get('image')
        article.save()
        messages.success(request, f"Article '{article.nom}' modifié avec succès.")
        return redirect('/bar/stock/?tab=articles')
    context = {'page_title': 'Modifier Article', 'article': article, 'categories': categories, 'unites': unites, 'mode': 'edit'}
    return render(request, 'bar/article_form.html', context)


@require_module_access('bar')
def article_delete(request, pk):
    article = get_object_or_404(BoissonBar, pk=pk)
    if request.method == 'POST':
        nom = article.nom
        article.statut = 'supprime'
        article.save()
        messages.success(request, f"Article '{nom}' supprimé.")
        return redirect('/bar/stock/?tab=articles')
    return render(request, 'bar/article_confirm_delete.html', {'article': article})


@require_module_access('bar')
def article_dupliquer(request, pk):
    article = get_object_or_404(BoissonBar, pk=pk)
    article.pk = None
    article.reference = None
    article.nom = f"{article.nom} (copie)"
    article.save()
    messages.success(request, "Article dupliqué avec succès.")
    return redirect('bar:article_edit', pk=article.pk)


@require_module_access('bar')
def article_sommeil(request, pk):
    article = get_object_or_404(BoissonBar, pk=pk)
    if article.statut == 'actif':
        article.statut = 'sommeil'
        msg = f"Article '{article.nom}' mis en sommeil."
    else:
        article.statut = 'actif'
        msg = f"Article '{article.nom}' réactivé."
    article.save()
    messages.success(request, msg)
    return redirect('/bar/stock/?tab=articles')


# ===== BONS DE COMMANDE =====

@require_module_access('bar')
def bon_commande_list(request):
    return redirect('/bar/stock/?tab=commandes')


@require_module_access('bar')
def bon_commande_create(request):
    type_commande = request.GET.get('type', 'achat')
    fournisseurs = Fournisseur.objects.all()
    clients = Client.objects.filter(actif=True)
    articles = BoissonBar.objects.exclude(statut='supprime')

    if request.method == 'POST':
        type_cmd = request.POST.get('type_commande', 'achat')
        bon = BonCommandeBar(
            type_commande=type_cmd,
            statut=request.POST.get('statut', 'brouillon'),
            fournisseur_id=request.POST.get('fournisseur') or None,
            client_id=request.POST.get('client') or None,
            date_commande=request.POST.get('date_commande') or timezone.now().date(),
            date_livraison_prevue=request.POST.get('date_livraison_prevue') or None,
            notes=request.POST.get('notes', ''),
            cree_par=request.user,
        )
        bon.save()

        # Lignes
        article_ids = request.POST.getlist('article_id[]')
        quantites = request.POST.getlist('quantite[]')
        prix_list = request.POST.getlist('prix_unitaire[]')
        notes_list = request.POST.getlist('notes_ligne[]')

        for i, art_id in enumerate(article_ids):
            if art_id and quantites[i]:
                LigneBonCommandeBar.objects.create(
                    bon=bon,
                    article_id=art_id,
                    quantite_commandee=quantites[i],
                    prix_unitaire=prix_list[i] if prix_list[i] else 0,
                    notes_ligne=notes_list[i] if i < len(notes_list) else '',
                )

        messages.success(request, f"Bon de commande {bon.numero} créé avec succès.")
        return redirect(f'/bar/stock/?tab=commandes')

    context = {
        'page_title': 'Nouveau Bon de Commande',
        'type_commande': type_commande,
        'fournisseurs': fournisseurs,
        'clients': clients,
        'articles': articles,
        'mode': 'create',
    }
    return render(request, 'bar/bon_commande_form.html', context)


@require_module_access('bar')
def bon_commande_detail(request, pk):
    bon = get_object_or_404(BonCommandeBar, pk=pk)
    lignes = bon.lignes.select_related('article').all()
    context = {
        'page_title': f'Bon {bon.numero}',
        'bon': bon,
        'lignes': lignes,
    }
    return render(request, 'bar/bon_commande_detail.html', context)


@require_module_access('bar')
def bon_commande_edit(request, pk):
    bon = get_object_or_404(BonCommandeBar, pk=pk)
    fournisseurs = Fournisseur.objects.all()
    clients = Client.objects.filter(actif=True)
    articles = BoissonBar.objects.exclude(statut='supprime')

    if request.method == 'POST':
        bon.statut = request.POST.get('statut', bon.statut)
        bon.fournisseur_id = request.POST.get('fournisseur') or None
        bon.client_id = request.POST.get('client') or None
        bon.date_commande = request.POST.get('date_commande') or bon.date_commande
        bon.date_livraison_prevue = request.POST.get('date_livraison_prevue') or None
        bon.notes = request.POST.get('notes', '')
        bon.save()

        # Mise à jour lignes
        bon.lignes.all().delete()
        article_ids = request.POST.getlist('article_id[]')
        quantites = request.POST.getlist('quantite[]')
        prix_list = request.POST.getlist('prix_unitaire[]')
        notes_list = request.POST.getlist('notes_ligne[]')

        for i, art_id in enumerate(article_ids):
            if art_id and quantites[i]:
                LigneBonCommandeBar.objects.create(
                    bon=bon,
                    article_id=art_id,
                    quantite_commandee=quantites[i],
                    prix_unitaire=prix_list[i] if prix_list[i] else 0,
                    notes_ligne=notes_list[i] if i < len(notes_list) else '',
                )

        messages.success(request, f"Bon {bon.numero} modifié avec succès.")
        return redirect(f'/bar/stock/?tab=commandes')

    context = {
        'page_title': f'Modifier {bon.numero}',
        'bon': bon,
        'lignes': bon.lignes.all(),
        'fournisseurs': fournisseurs,
        'clients': clients,
        'articles': articles,
        'mode': 'edit',
    }
    return render(request, 'bar/bon_commande_form.html', context)


@require_module_access('bar')
def bon_commande_annuler(request, pk):
    bon = get_object_or_404(BonCommandeBar, pk=pk)
    if request.method == 'POST':
        bon.statut = 'annule'
        bon.save()
        messages.warning(request, f"Bon {bon.numero} annulé.")
    return redirect('/bar/stock/?tab=commandes')


@require_module_access('bar')
def bon_commande_changer_statut(request, pk):
    """AJAX : changer le statut d'un bon"""
    if request.method == 'POST':
        bon = get_object_or_404(BonCommandeBar, pk=pk)
        nouveau_statut = request.POST.get('statut')
        statuts_valides = [s[0] for s in BonCommandeBar.STATUT_CHOICES]
        if nouveau_statut in statuts_valides:
            bon.statut = nouveau_statut
            bon.save()
            return JsonResponse({'success': True, 'statut': bon.statut, 'numero': bon.numero})
    return JsonResponse({'success': False}, status=400)


@require_module_access('bar')
def get_article_prix(request, pk):
    """AJAX : récupérer le prix d'achat d'un article"""
    article = get_object_or_404(BoissonBar, pk=pk)
    return JsonResponse({
        'prix_achat': float(article.prix_achat),
        'prix_vente': float(article.prix),
        'unite': article.unite_affichee,
        'reference': article.reference or '',
    })


# ===== BONS DE RÉCEPTION =====

@require_module_access('bar')
def bon_reception_list(request):
    return redirect('/bar/stock/?tab=reception')


@require_module_access('bar')
def bon_reception_create(request):
    fournisseurs = Fournisseur.objects.all()
    articles = BoissonBar.objects.exclude(statut='supprime')
    bons_commande = BonCommandeBar.objects.filter(
        type_commande='achat',
        statut__in=['confirme', 'envoye', 'partiel']
    ).order_by('-date_commande')

    if request.method == 'POST':
        bon_commande_id = request.POST.get('bon_commande') or None
        br = BonReceptionBar(
            bon_commande_id=bon_commande_id,
            fournisseur_id=request.POST.get('fournisseur') or None,
            numero_document_fournisseur=request.POST.get('numero_document_fournisseur', ''),
            operateur=request.user,
            date_reception=request.POST.get('date_reception') or timezone.now().date(),
            statut=request.POST.get('statut', 'brouillon'),
            notes=request.POST.get('notes', ''),
        )
        br.save()

        article_ids = request.POST.getlist('article_id[]')
        qtes_commandees = request.POST.getlist('quantite_commandee[]')
        qtes_recues = request.POST.getlist('quantite_recue[]')
        prix_list = request.POST.getlist('prix_unitaire[]')
        notes_list = request.POST.getlist('notes_ligne[]')

        for i, art_id in enumerate(article_ids):
            if art_id and qtes_recues[i]:
                LigneBonReceptionBar.objects.create(
                    bon=br,
                    article_id=art_id,
                    quantite_commandee=qtes_commandees[i] if qtes_commandees[i] else 0,
                    quantite_recue=qtes_recues[i],
                    prix_unitaire=prix_list[i] if prix_list[i] else 0,
                    notes_ligne=notes_list[i] if i < len(notes_list) else '',
                )

        # Si statut = validé → mettre à jour le stock
        if br.statut == 'valide':
            _valider_reception(br, request.user)

        messages.success(request, f"Bon de réception {br.numero} créé avec succès.")
        return redirect('/bar/stock/?tab=reception')

    # Pré-remplir depuis un bon de commande si fourni
    bc_id = request.GET.get('bc', None)
    bc_prefill = None
    if bc_id:
        bc_prefill = BonCommandeBar.objects.filter(pk=bc_id).first()

    context = {
        'page_title': 'Nouveau Bon de Réception',
        'fournisseurs': fournisseurs,
        'articles': articles,
        'bons_commande': bons_commande,
        'bc_prefill': bc_prefill,
        'mode': 'create',
    }
    return render(request, 'bar/bon_reception_form.html', context)


@require_module_access('bar')
def bon_reception_detail(request, pk):
    br = get_object_or_404(BonReceptionBar, pk=pk)
    lignes = br.lignes.select_related('article').all()
    context = {
        'page_title': f'Réception {br.numero}',
        'br': br,
        'lignes': lignes,
    }
    return render(request, 'bar/bon_reception_detail.html', context)


@require_module_access('bar')
def bon_reception_valider(request, pk):
    """Valider un bon de réception → mise à jour stock + CMUP"""
    br = get_object_or_404(BonReceptionBar, pk=pk)
    if request.method == 'POST':
        if br.statut in ['brouillon', 'en_cours']:
            _valider_reception(br, request.user)
            messages.success(request, f"Bon {br.numero} validé. Stock mis à jour.")
        else:
            messages.warning(request, "Ce bon ne peut pas être validé dans son état actuel.")
    return redirect('/bar/stock/?tab=reception')


def _valider_reception(br, user):
    """Fonction interne : valider réception et mettre à jour stock + CMUP"""
    for ligne in br.lignes.all():
        article = ligne.article
        qte = ligne.quantite_recue
        prix = ligne.prix_unitaire

        # Calcul CMUP
        if qte > 0 and prix > 0:
            valeur_actuelle = article.quantite_stock * article.prix_achat
            valeur_nouvelle = float(qte) * float(prix)
            nouvelle_qte = article.quantite_stock + int(qte)
            if nouvelle_qte > 0:
                article.prix_achat = (valeur_actuelle + valeur_nouvelle) / nouvelle_qte

        # Mise à jour stock
        MouvementStockBar.objects.create(
            boisson=article,
            type_mouvement='entree',
            quantite=int(qte),
            commentaire=f"Réception {br.numero} — {br.fournisseur or 'Sans fournisseur'}",
            utilisateur=user,
        )

    # Mettre à jour le statut du bon de commande lié si réception totale
    if br.bon_commande:
        bc = br.bon_commande
        total_recu = sum(
            sum(l.quantite_recue for l in reception.lignes.all())
            for reception in bc.receptions.filter(statut='valide')
        )
        total_commande = sum(l.quantite_commandee for l in bc.lignes.all())
        if total_recu >= total_commande:
            bc.statut = 'recu'
        else:
            bc.statut = 'partiel'
        bc.save()

    br.statut = 'valide'
    br.date_validation = timezone.now()
    br.valide_par = user
    br.save()


@require_module_access('bar')
def bon_reception_annuler(request, pk):
    br = get_object_or_404(BonReceptionBar, pk=pk)
    if request.method == 'POST':
        if br.statut != 'valide':
            br.statut = 'annule'
            br.save()
            messages.warning(request, f"Bon {br.numero} annulé.")
        else:
            messages.error(request, "Impossible d'annuler un bon déjà validé.")
    return redirect('/bar/stock/?tab=reception')


@require_module_access('bar')
def get_bon_commande_lignes(request, pk):
    """AJAX : récupérer les lignes d'un bon de commande pour pré-remplir la réception"""
    bc = get_object_or_404(BonCommandeBar, pk=pk)
    lignes = []
    for l in bc.lignes.select_related('article').all():
        lignes.append({
            'article_id': l.article_id,
            'article_nom': l.article.nom,
            'article_ref': l.article.reference or '',
            'quantite_commandee': float(l.quantite_commandee),
            'reliquat': float(l.reliquat),
            'prix_unitaire': float(l.prix_unitaire),
        })
    return JsonResponse({
        'lignes': lignes,
        'fournisseur_id': bc.fournisseur_id or '',
        'fournisseur_nom': str(bc.fournisseur) if bc.fournisseur else '',
        'numero': bc.numero,
    })


# ===== MOUVEMENTS ENTRÉES / SORTIES =====

@require_module_access('bar')
def mouvement_create(request):
    """Créer un mouvement manuel depuis le modal"""
    if request.method == 'POST':
        boisson_id = request.POST.get('boisson_id')
        type_mv = request.POST.get('type_mouvement')
        quantite = request.POST.get('quantite', 0)
        commentaire = request.POST.get('commentaire', '')

        TYPE_LABELS = {
            'entree': 'Entrée manuelle',
            'sortie': 'Sortie manuelle',
            'casse': 'Casse / Perte',
            'inventaire': 'Ajustement inventaire',
        }

        try:
            boisson = BoissonBar.objects.get(pk=boisson_id)
            MouvementStockBar.objects.create(
                boisson=boisson,
                type_mouvement=type_mv,
                quantite=int(quantite),
                commentaire=commentaire or TYPE_LABELS.get(type_mv, type_mv),
                utilisateur=request.user,
            )
            messages.success(request, f"Mouvement enregistré : {boisson.nom} ({type_mv})")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")

    return redirect('/bar/stock/?tab=mouvements')


# ===== INVENTAIRE =====

@require_module_access('bar')
def inventaire_list(request):
    return redirect('/bar/stock/?tab=inventaire')


@require_module_access('bar')
def inventaire_create(request):
    """Créer un nouvel inventaire avec toutes les boissons actives"""
    articles = BoissonBar.objects.exclude(statut='supprime').select_related('categorie')

    if request.method == 'POST':
        inv = InventaireBar(
            statut=request.POST.get('statut', 'brouillon'),
            notes=request.POST.get('notes', ''),
            cree_par=request.user,
        )
        inv.save()

        article_ids = request.POST.getlist('article_id[]')
        qtes_comptees = request.POST.getlist('quantite_comptee[]')
        qtes_theoriques = request.POST.getlist('quantite_theorique[]')
        prix_list = request.POST.getlist('prix_unitaire[]')
        notes_list = request.POST.getlist('notes_ligne[]')

        for i, art_id in enumerate(article_ids):
            if art_id:
                LigneInventaireBar.objects.create(
                    inventaire=inv,
                    article_id=art_id,
                    quantite_theorique=qtes_theoriques[i] if qtes_theoriques[i] else 0,
                    quantite_comptee=qtes_comptees[i] if qtes_comptees[i] else 0,
                    prix_unitaire=prix_list[i] if prix_list[i] else 0,
                    notes_ligne=notes_list[i] if i < len(notes_list) else '',
                )

        if inv.statut == 'valide':
            _valider_inventaire(inv, request.user)

        messages.success(request, f"Inventaire {inv.numero} créé.")
        return redirect('/bar/stock/?tab=inventaire')

    # Pré-remplir avec tous les articles actifs
    context = {
        'page_title': 'Nouvel Inventaire',
        'articles': articles,
        'mode': 'create',
    }
    return render(request, 'bar/inventaire_form.html', context)


@require_module_access('bar')
def inventaire_detail(request, pk):
    inv = get_object_or_404(InventaireBar, pk=pk)
    lignes = inv.lignes.select_related('article').order_by('article__categorie__nom', 'article__nom')
    ecarts = [l for l in lignes if l.ecart_quantite != 0]
    context = {
        'page_title': f'Inventaire {inv.numero}',
        'inv': inv,
        'lignes': lignes,
        'ecarts': ecarts,
        'valeur_ecart_total': sum(abs(l.valeur_ecart) for l in ecarts),
    }
    return render(request, 'bar/inventaire_detail.html', context)


@require_module_access('bar')
def inventaire_valider(request, pk):
    inv = get_object_or_404(InventaireBar, pk=pk)
    if request.method == 'POST' and inv.statut in ['brouillon', 'en_cours']:
        _valider_inventaire(inv, request.user)
        messages.success(request, f"Inventaire {inv.numero} validé. Stock ajusté.")
    return redirect('/bar/stock/?tab=inventaire')


def _valider_inventaire(inv, user):
    """Valider inventaire → créer mouvements d'ajustement pour chaque écart"""
    for ligne in inv.lignes.all():
        ecart = ligne.ecart_quantite
        if ecart != 0:
            # Créer un mouvement d'ajustement
            MouvementStockBar.objects.create(
                boisson=ligne.article,
                type_mouvement='inventaire',
                quantite=int(abs(ecart)),
                commentaire=f"Ajustement inventaire {inv.numero} — écart: {'+' if ecart > 0 else ''}{ecart}",
                utilisateur=user,
            )
            # Mettre à jour le stock directement si mouvement négatif
            if ecart < 0:
                ligne.article.quantite_stock += int(ecart)  # ecart est négatif
                ligne.article.save()

    inv.statut = 'valide'
    inv.date_validation = timezone.now()
    inv.valide_par = user
    inv.save()


@require_module_access('bar')
def inventaire_annuler(request, pk):
    inv = get_object_or_404(InventaireBar, pk=pk)
    if request.method == 'POST' and inv.statut != 'valide':
        inv.statut = 'annule'
        inv.save()
        messages.warning(request, f"Inventaire {inv.numero} annulé.")
    return redirect('/bar/stock/?tab=inventaire')


# ===== GESTION DES CASSES =====

@require_module_access('bar')
def casse_list(request):
    return redirect('/bar/stock/?tab=casses')


@require_module_access('bar')
def casse_create(request):
    articles = BoissonBar.objects.exclude(statut='supprime').select_related('categorie')

    if request.method == 'POST':
        casse = CasseBar(
            type_casse=request.POST.get('type_casse', 'casse'),
            statut='declare',
            declare_par=request.user,
            date_casse=request.POST.get('date_casse') or timezone.now().date(),
            description=request.POST.get('description', ''),
        )
        casse.save()

        article_ids = request.POST.getlist('article_id[]')
        quantites = request.POST.getlist('quantite[]')
        prix_list = request.POST.getlist('prix_unitaire[]')
        notes_list = request.POST.getlist('notes_ligne[]')

        for i, art_id in enumerate(article_ids):
            if art_id and quantites[i]:
                LigneCasseBar.objects.create(
                    casse=casse,
                    article_id=art_id,
                    quantite=quantites[i],
                    prix_unitaire=prix_list[i] if prix_list[i] else 0,
                    notes_ligne=notes_list[i] if i < len(notes_list) else '',
                )

        # Valider immédiatement si demandé
        if request.POST.get('valider_maintenant') == '1':
            _valider_casse(casse, request.user)
            messages.success(request, f"Casse {casse.numero} déclarée et validée. Stock mis à jour.")
        else:
            messages.success(request, f"Casse {casse.numero} déclarée. En attente de validation.")

        return redirect('/bar/stock/?tab=casses')

    context = {
        'page_title': 'Déclarer une Casse / Perte',
        'articles': articles,
    }
    return render(request, 'bar/casse_form.html', context)


@require_module_access('bar')
def casse_detail(request, pk):
    casse = get_object_or_404(CasseBar, pk=pk)
    lignes = casse.lignes.select_related('article').all()
    context = {
        'page_title': f'Casse {casse.numero}',
        'casse': casse,
        'lignes': lignes,
    }
    return render(request, 'bar/casse_detail.html', context)


@require_module_access('bar')
def casse_valider(request, pk):
    casse = get_object_or_404(CasseBar, pk=pk)
    if request.method == 'POST' and casse.statut == 'declare':
        _valider_casse(casse, request.user)
        messages.success(request, f"Casse {casse.numero} validée. Stock mis à jour.")
    return redirect('/bar/stock/?tab=casses')


def _valider_casse(casse, user):
    """Valider une casse → déduire du stock + créer mouvements tracés"""
    for ligne in casse.lignes.all():
        MouvementStockBar.objects.create(
            boisson=ligne.article,
            type_mouvement='casse',
            quantite=int(ligne.quantite),
            commentaire=f"{casse.get_type_casse_display()} — {casse.numero} — {casse.description[:50] if casse.description else ''}",
            utilisateur=user,
        )
    casse.statut = 'valide'
    casse.date_validation = timezone.now()
    casse.valide_par = user
    casse.save()


@require_module_access('bar')
def casse_annuler(request, pk):
    casse = get_object_or_404(CasseBar, pk=pk)
    if request.method == 'POST' and casse.statut == 'declare':
        casse.statut = 'annule'
        casse.save()
        messages.warning(request, f"Déclaration {casse.numero} annulée.")
    return redirect('/bar/stock/?tab=casses')

@require_module_access('bar')
def rapport_stock_cave(request):
    get = request.GET.copy()
    if 'module' not in get:
        get['module'] = 'cave'
    request.GET = get
    from rapport.views import rapport_stock
    return rapport_stock(request)


# ================================================================
# REMPLACEMENT DE bar_tpe dans bar/views.py
# ================================================================

@require_module_access('bar')
def bar_tpe(request):
    from .models import BoissonBar, CategorieBar
    from django.contrib.auth.models import User, Group
    from dashboard.models import Configuration

    boissons   = BoissonBar.objects.select_related('categorie').filter(
        statut='actif', disponible=True
    ).order_by('categorie__nom', 'nom')
    categories = CategorieBar.objects.order_by('nom')

    # Groupe exact en base : "Serveuse/Serveur" (id=5)
    try:
        groupe_serveurs = Group.objects.get(name='Serveuse/Serveur')
        serveurs = User.objects.filter(
            groups=groupe_serveurs,
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
    except Group.DoesNotExist:
        serveurs = User.objects.none()

    config = Configuration.load()

    return render(request, 'bar/index.html', {
        'boissons'   : boissons,
        'categories' : categories,
        'serveurs'   : serveurs,
        'config'     : config,
        'page_title' : 'Cave - Vente TPE',
    })


import json
import json
from decimal import Decimal

@require_module_access('bar')
@require_POST
def api_vente_create(request):
    """
    API AJAX appelée depuis le TPE Cave.
    POST JSON -> crée Ticket facturation + décrémente stock BoissonBar.
    """
    try:
        data         = json.loads(request.body)
        lignes       = data.get('lignes', [])
        total        = Decimal(str(data.get('total', 0)))
        paiement     = data.get('paiement', 'especes')
        espace       = data.get('espace', '')
        ref          = data.get('ref', '')
        ticket_nom   = data.get('ticket_nom', 'T-???')
        montant_recu = Decimal(str(data.get('montant_recu', total)))

        if not lignes:
            return JsonResponse({'ok': False, 'error': 'Ticket vide'}, status=400)

        # Map mode paiement TPE -> choix Ticket facturation
        MODE_MAP = {
            'especes': 'especes',
            'carte'  : 'carte_bancaire',
            'mobile' : 'mobile_money',
            'chambre': 'autre',
        }
        mode_fact = MODE_MAP.get(paiement, 'especes')

        ESPACE_LABELS = {
            'restaurant'  : 'Restaurant',
            'piscine'     : 'Piscine',
            'evenementiel': 'Espace evenementiel',
            'hotel'       : 'Hotel',
            'comptoir'    : 'Bar comptoir',
            'plage'       : 'Plage',
            'visite'      : 'Visiteur',
        }
        espace_label = ESPACE_LABELS.get(espace, espace or 'Cave')
        rendu        = max(Decimal('0'), montant_recu - total)

        # Construire le contenu texte lisible du ticket
        from django.utils import timezone as tz
        date_str  = tz.now().strftime('%d/%m/%Y %H:%M')
        lignes_txt = "\n".join(
            f"  {l['nom']} x{l['qty']}  {int(Decimal(str(l['prix'])) * int(l['qty'])):,} F"
            for l in lignes
        )
        contenu = (
            f"COMPLEXE BEHANIAN - Cave\n"
            f"Ticket  : {ticket_nom}\n"
            f"Date    : {date_str}\n"
            f"Espace  : {espace_label}\n"
            f"Ref     : {ref or '-'}\n"
            f"{'='*32}\n"
            f"{lignes_txt}\n"
            f"{'='*32}\n"
            f"TOTAL   : {int(total):,} FCFA\n"
            f"Reglement : {mode_fact}\n"
        )
        if paiement in ('especes', 'mobile') and rendu > 0:
            contenu += f"Recu    : {int(montant_recu):,} F\n"
            contenu += f"Rendu   : {int(rendu):,} F\n"

        # Creer le Ticket dans facturation
        from facturation.models import Ticket, generate_ticket_numero
        ticket = Ticket.objects.create(
            numero        = generate_ticket_numero(),
            module        = 'cave',
            montant_total = total,
            mode_paiement = mode_fact,
            montant_paye  = montant_recu,
            contenu       = contenu,
            cree_par      = request.user,
            imprime       = True,
            date_impression = tz.now(),
        )

        # Decrementer stock + tracer mouvements
        erreurs_stock = []
        for l in lignes:
            try:
                boisson = BoissonBar.objects.get(pk=int(l['id']))
                qty     = int(l['qty'])
                if boisson.quantite_stock < qty:
                    erreurs_stock.append(
                        f"{boisson.nom}: stock insuffisant ({boisson.quantite_stock} dispo, {qty} demande)"
                    )
                    # On continue quand même (vente enregistrée)
                MouvementStockBar.objects.create(
                    boisson        = boisson,
                    type_mouvement = 'sortie',
                    quantite       = qty,
                    commentaire    = f"Vente TPE - {ticket.numero} - {espace_label} {ref}".strip(' -'),
                    utilisateur    = request.user,
                )
            except BoissonBar.DoesNotExist:
                erreurs_stock.append(f"Article id={l['id']} introuvable")

        return JsonResponse({
            'ok'            : True,
            'ticket_id'     : ticket.pk,
            'ticket_numero' : ticket.numero,
            'total'         : int(total),
            'rendu'         : int(rendu),
            'erreurs_stock' : erreurs_stock,
        })

    except Exception as e:
        import traceback
        return JsonResponse({'ok': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)





