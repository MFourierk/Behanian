from django.urls import path
from . import views
from .views_export import export_stock_excel

app_name = 'cuisine'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Articles & Fournisseurs
    path('articles/', views.article_list, name='article_list'),
    path('articles/create/modal/', views.article_create_modal, name='article_create_modal'),
    path('articles/<int:pk>/edit/', views.article_edit, name='article_edit'),
    path('fournisseurs/', views.fournisseur_list, name='fournisseur_list'),

    # Bons de Réception (Entrées de stock)
    path('reception/', views.bon_reception_list, name='bon_reception_list'),
    path('reception/nouveau/', views.bon_reception_create, name='bon_reception_create'),
    path('reception/<int:pk>/', views.bon_reception_detail, name='bon_reception_detail'),
    path('reception/<int:pk>/print/', views.bon_reception_print, name='bon_reception_print'),

    # Mouvements & Stock
    path('mouvement-stock/', views.mouvement_stock, name='mouvement_stock'),
    path('transformation-stock/', views.transformation_stock, name='transformation_stock'),
    path('etat-stock/', views.etat_stock, name='etat_stock'),
    path('etat-stock/export/', export_stock_excel, name='export_stock_excel'),
    path('inventaire/', views.inventaire_saisie, name='inventaire_saisie'),

    # Recettes
    path('recettes/', views.recette_list, name='recette_list'),
    path('recettes/create/', views.recette_create, name='recette_create'),
    path('recettes/create/modal/', views.recette_create_modal, name='recette_create_modal'),

    path('recettes/<int:pk>/edit/', views.recette_edit, name='recette_edit'),
    path('recettes/<int:pk>/delete/', views.recette_delete, name='recette_delete'),
    path('recettes/edit-form/<int:pk>/', views.recette_edit_get_form, name='recette_edit_get_form'),

    # Rapports & Analyses
    path('rapports/', views.rapports_dashboard, name='rapports_dashboard'),
    path('rapports/consommation/', views.rapport_consommation, name='report_consommation'),
    path('rapports/pertes/', views.rapport_pertes, name='report_pertes'),

    # API pour les graphiques
    path('api/chart/mouvements/', views.chart_data_mouvements, name='chart_data_mouvements'),
    path('api/chart/top-consommation/', views.chart_data_top_consommation, name='chart_data_top_consommation'),
    path('api/ingredient-details/<int:ingredient_id>/', views.get_ingredient_details, name='get_ingredient_details'),
    path('api/ingredients-details/', views.get_ingredients_details, name='get_ingredients_details'),
]
