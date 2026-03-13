# ==============================================================
# RAPPORT DE STOCK — COMPLEXE BEHANIAN
# ==============================================================
# Fichier : rapport/views.py  (ou ajouter dans dashboard/views.py)
#
# Accessible depuis :
#   /rapport/stock/              → rapport complet
#   /cuisine/rapport/stock/      → filtré sur Cuisine par défaut
#   /cave/rapport/stock/         → filtré sur Cave par défaut
# ==============================================================

from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal

# Imports Cuisine
from cuisine.models import Ingredient, CategorieIngredient

# Imports Cave / Bar
from bar.models import BoissonBar, CategorieBar


def rapport_stock(request):
    """
    Rapport de stock unifié — Cuisine + Cave.
    Filtres : module, catégorie, date (snapshot), état.
    """

    # --- Paramètres GET ---
    module_filtre    = request.GET.get('module', 'tous')      # cuisine / cave / tous
    categorie_filtre = request.GET.get('categorie', '')       # pk de la catégorie
    etat_filtre      = request.GET.get('etat', 'tous')        # tous / bas / rupture
    date_rapport     = request.GET.get('date', timezone.now().date().isoformat())

    # Pour l'instant le stock est en temps réel (snapshot live).
    # Une future évolution pourra interroger MouvementStock pour reconstruire
    # le stock à une date donnée — la vue est déjà prête pour ça.

    # -------------------------------------------------------
    # CUISINE — Ingrédients
    # -------------------------------------------------------
    ingredients = []
    total_valeur_cuisine = Decimal('0')

    if module_filtre in ('cuisine', 'tous'):
        qs_cuisine = Ingredient.objects.select_related(
            'categorie', 'unite_stock', 'fournisseur_principal'
        ).filter(statut=True).order_by('categorie__ordre', 'categorie__nom', 'nom')

        if categorie_filtre and module_filtre == 'cuisine':
            qs_cuisine = qs_cuisine.filter(categorie__pk=categorie_filtre)

        for ing in qs_cuisine:
            valeur = ing.quantite_stock * ing.cmup

            if etat_filtre == 'rupture' and not ing.est_en_rupture:
                continue
            if etat_filtre == 'bas' and not (ing.est_stock_bas or ing.est_en_rupture):
                continue

            etat = 'rupture' if ing.est_en_rupture else ('bas' if ing.est_stock_bas else 'normal')
            total_valeur_cuisine += valeur

            ingredients.append({
                'module'     : 'cuisine',
                'reference'  : ing.reference or '—',
                'nom'        : ing.nom,
                'categorie'  : ing.categorie.nom if ing.categorie else 'Sans catégorie',
                'categorie_ordre': ing.categorie.ordre if ing.categorie else 999,
                'quantite'   : ing.quantite_stock,
                'unite'      : str(ing.unite_stock) if ing.unite_stock else '—',
                'cmup'       : ing.cmup,
                'valeur'     : valeur,
                'seuil'      : ing.seuil_alerte,
                'stock_max'  : ing.stock_max,
                'fournisseur': str(ing.fournisseur_principal) if ing.fournisseur_principal else '—',
                'etat'       : etat,
            })

    # -------------------------------------------------------
    # CAVE — Boissons
    # -------------------------------------------------------
    total_valeur_cave = Decimal('0')
    boissons = []

    if module_filtre in ('cave', 'tous'):
        qs_cave = BoissonBar.objects.select_related(
            'categorie'
        ).filter(statut='actif').order_by('categorie__nom', 'nom')

        if categorie_filtre and module_filtre == 'cave':
            qs_cave = qs_cave.filter(categorie__pk=categorie_filtre)

        for b in qs_cave:
            valeur = Decimal(b.quantite_stock) * b.prix_achat

            if etat_filtre == 'rupture' and not b.est_en_rupture:
                continue
            if etat_filtre == 'bas' and not (b.est_stock_bas or b.est_en_rupture):
                continue

            etat = 'rupture' if b.est_en_rupture else ('bas' if b.est_stock_bas else 'normal')
            total_valeur_cave += valeur

            boissons.append({
                'module'     : 'cave',
                'reference'  : b.reference or '—',
                'nom'        : b.nom,
                'categorie'  : b.categorie.nom if b.categorie else 'Sans catégorie',
                'categorie_ordre': 0,
                'quantite'   : b.quantite_stock,
                'unite'      : b.unite_affichee,
                'cmup'       : b.prix_achat,   # Pour la cave : prix achat = coût unitaire
                'valeur'     : valeur,
                'seuil'      : b.seuil_alerte,
                'stock_max'  : 0,
                'fournisseur': '—',
                'etat'       : etat,
            })

    # -------------------------------------------------------
    # Fusion + regroupement par module > catégorie
    # -------------------------------------------------------
    tous_articles = ingredients + boissons

    # Regroupement pour le template
    groupes = {}
    for art in tous_articles:
        cle = (art['module'], art['categorie'])
        if cle not in groupes:
            groupes[cle] = {
                'module'    : art['module'],
                'categorie' : art['categorie'],
                'articles'  : [],
                'valeur'    : Decimal('0'),
                'nb_rupture': 0,
                'nb_bas'    : 0,
            }
        groupes[cle]['articles'].append(art)
        groupes[cle]['valeur'] += art['valeur']
        if art['etat'] == 'rupture': groupes[cle]['nb_rupture'] += 1
        if art['etat'] == 'bas':     groupes[cle]['nb_bas'] += 1

    groupes_list = sorted(groupes.values(), key=lambda g: (g['module'], g['categorie']))

    # -------------------------------------------------------
    # Statistiques globales
    # -------------------------------------------------------
    total_articles  = len(tous_articles)
    nb_rupture      = sum(1 for a in tous_articles if a['etat'] == 'rupture')
    nb_bas          = sum(1 for a in tous_articles if a['etat'] == 'bas')
    nb_normal       = total_articles - nb_rupture - nb_bas
    total_valeur    = total_valeur_cuisine + total_valeur_cave

    # -------------------------------------------------------
    # Listes pour les filtres
    # -------------------------------------------------------
    categories_cuisine = CategorieIngredient.objects.order_by('ordre', 'nom')
    categories_cave    = CategorieBar.objects.order_by('nom')

    context = {
        'page_title'          : 'Rapport de Stock',

        # Données
        'groupes'             : groupes_list,

        # Stats
        'total_articles'      : total_articles,
        'nb_rupture'          : nb_rupture,
        'nb_bas'              : nb_bas,
        'nb_normal'           : nb_normal,
        'total_valeur'        : total_valeur,
        'total_valeur_cuisine': total_valeur_cuisine,
        'total_valeur_cave'   : total_valeur_cave,

        # Filtres actifs (pour pré-remplir les selects)
        'module_filtre'       : module_filtre,
        'categorie_filtre'    : categorie_filtre,
        'etat_filtre'         : etat_filtre,
        'date_rapport'        : date_rapport,

        # Listes filtres
        'categories_cuisine'  : categories_cuisine,
        'categories_cave'     : categories_cave,

        # Date/heure du rapport
        'generated_at'        : timezone.now(),
    }

    return render(request, 'rapport/stock.html', context)
