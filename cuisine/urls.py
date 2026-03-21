from django.urls import path
from . import views

app_name = 'cuisine'

urlpatterns = [
    # Tableau de bord
    path('', views.index, name='index'),

    # Stock (page principale avec onglets)
    path('stock/', views.stock_management, name='stock_management'),

    # Ingrédients
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/nouveau/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/modifier/', views.ingredient_edit, name='ingredient_edit'),
    path('ingredients/<int:pk>/supprimer/', views.ingredient_delete, name='ingredient_delete'),

    # Mouvements de stock
    path('mouvement/nouveau/', views.mouvement_create, name='mouvement_create'),

    # Bons de commande
    path('commandes/', views.bon_commande_list, name='bon_commande_list'),
    path('commandes/nouveau/', views.bon_commande_create, name='bon_commande_create'),
    path('commandes/<int:pk>/', views.bon_commande_detail, name='bon_commande_detail'),
    path('commandes/<int:pk>/annuler/', views.bon_commande_annuler, name='bon_commande_annuler'),

    # Bons de réception
    path('receptions/', views.bon_reception_list, name='bon_reception_list'),
    path('receptions/nouveau/', views.bon_reception_create, name='bon_reception_create'),
    path('receptions/<int:pk>/', views.bon_reception_detail, name='bon_reception_detail'),
    path('receptions/<int:pk>/valider/', views.bon_reception_valider, name='bon_reception_valider'),
    path('receptions/<int:pk>/annuler/', views.bon_reception_annuler, name='bon_reception_annuler'),
    path('receptions/<int:pk>/print/', views.bon_reception_print, name='bon_reception_print'),

    # Fiches techniques
    path('fiches/', views.fiche_list, name='fiche_list'),
    path('fiches/nouveau/', views.fiche_create, name='fiche_create'),
    path('fiches/<int:pk>/', views.fiche_detail, name='fiche_detail'),
    path('fiches/<int:pk>/modifier/', views.fiche_edit, name='fiche_edit'),
    path('fiches/<int:pk>/supprimer/', views.fiche_delete, name='fiche_delete'),

    # Plats / Carte
    path('plats/', views.plat_list, name='plat_list'),
    path('plats/nouveau/', views.plat_create, name='plat_create'),
    path('plats/<int:pk>/modifier/', views.plat_edit, name='plat_edit'),
    path('plats/<int:pk>/supprimer/', views.plat_delete, name='plat_delete'),

    # Fournisseurs
    path('fournisseurs/', views.fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/nouveau/', views.fournisseur_create, name='fournisseur_create'),
    path('fournisseurs/<int:pk>/modifier/', views.fournisseur_edit, name='fournisseur_edit'),
    path('fournisseurs/<int:pk>/supprimer/', views.fournisseur_delete, name='fournisseur_delete'),

    # Inventaire
    path('inventaire/nouveau/', views.inventaire_create, name='inventaire_create'),
    path('inventaire/<int:pk>/valider/', views.inventaire_valider, name='inventaire_valider'),

    # Casses
    path('casses/nouveau/', views.casse_create, name='casse_create'),
    path('casses/<int:pk>/valider/', views.casse_valider, name='casse_valider'),

    # AJAX
    path('rapport/stock/', views.rapport_stock_cuisine, name='rapport_stock'),
    path('api/ingredient/<int:pk>/prix/', views.get_ingredient_prix, name='get_ingredient_prix'),
    path('rapport/stock/', views.rapport_stock_cuisine, name='rapport_stock'),
    path('api/commande/<int:pk>/lignes/', views.get_bc_lignes, name='get_bc_lignes'),
]
