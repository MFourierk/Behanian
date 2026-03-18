from django.urls import path
from . import views

app_name = 'bar'

urlpatterns = [
    path('tpe/', views.bar_tpe, name='tpe'),
    path('', views.bar_dashboard, name='dashboard'),
    path('stock/', views.stock_management, name='stock_management'),

    # Articles
    path('articles/', views.articles_list, name='articles_list'),
    path('articles/nouveau/', views.article_create, name='article_create'),
    path('articles/<int:pk>/modifier/', views.article_edit, name='article_edit'),
    path('articles/<int:pk>/supprimer/', views.article_delete, name='article_delete'),
    path('articles/<int:pk>/dupliquer/', views.article_dupliquer, name='article_dupliquer'),
    path('articles/<int:pk>/sommeil/', views.article_sommeil, name='article_sommeil'),
    path('articles/<int:pk>/prix/', views.get_article_prix, name='article_prix_ajax'),

    # Bons de commande
    path('commandes/', views.bon_commande_list, name='bon_commande_list'),
    path('commandes/nouveau/', views.bon_commande_create, name='bon_commande_create'),
    path('commandes/<int:pk>/', views.bon_commande_detail, name='bon_commande_detail'),
    path('commandes/<int:pk>/modifier/', views.bon_commande_edit, name='bon_commande_edit'),
    path('commandes/<int:pk>/annuler/', views.bon_commande_annuler, name='bon_commande_annuler'),
    path('commandes/<int:pk>/statut/', views.bon_commande_changer_statut, name='bon_commande_statut'),
    path('commandes/<int:pk>/lignes/', views.get_bon_commande_lignes, name='bon_commande_lignes_ajax'),

    # Bons de réception
    path('receptions/', views.bon_reception_list, name='bon_reception_list'),
    path('receptions/nouveau/', views.bon_reception_create, name='bon_reception_create'),
    path('receptions/<int:pk>/', views.bon_reception_detail, name='bon_reception_detail'),
    path('receptions/<int:pk>/valider/', views.bon_reception_valider, name='bon_reception_valider'),
    path('receptions/<int:pk>/annuler/', views.bon_reception_annuler, name='bon_reception_annuler'),

    # Mouvements
    path('mouvements/nouveau/', views.mouvement_create, name='mouvement_create'),

    # Inventaire
    path('inventaire/', views.inventaire_list, name='inventaire_list'),
    path('inventaire/nouveau/', views.inventaire_create, name='inventaire_create'),
    path('inventaire/<int:pk>/', views.inventaire_detail, name='inventaire_detail'),
    path('inventaire/<int:pk>/valider/', views.inventaire_valider, name='inventaire_valider'),
    path('inventaire/<int:pk>/annuler/', views.inventaire_annuler, name='inventaire_annuler'),

    # Casses
    path('api/vente/', views.api_vente_create, name='api_vente'),
    path('rapport/stock/', views.rapport_stock_cave, name='rapport_stock'),
    path('casses/', views.casse_list, name='casse_list'),
    path('casses/nouveau/', views.casse_create, name='casse_create'),
    path('casses/<int:pk>/', views.casse_detail, name='casse_detail'),
    path('casses/<int:pk>/valider/', views.casse_valider, name='casse_valider'),
    path('casses/<int:pk>/annuler/', views.casse_annuler, name='casse_annuler'),
]


