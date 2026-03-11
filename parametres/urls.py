from django.urls import path
from . import views

app_name = 'parametres'

urlpatterns = [
    path('', views.parametres_index, name='parametres_index'),
    
    # Hotel - Chambres
    path('chambres/', views.ChambreListView.as_view(), name='chambre_list'),
    path('chambres/ajouter/', views.ChambreCreateView.as_view(), name='chambre_create'),
    path('chambres/<int:pk>/modifier/', views.ChambreUpdateView.as_view(), name='chambre_update'),
    path('chambres/<int:pk>/supprimer/', views.ChambreDeleteView.as_view(), name='chambre_delete'),

    # Bar - Boissons
    path('bar/boissons/', views.BoissonBarListView.as_view(), name='boissonbar_list'),
    path('bar/boissons/ajouter/', views.BoissonBarCreateView.as_view(), name='boissonbar_create'),
    path('bar/boissons/<int:pk>/modifier/', views.BoissonBarUpdateView.as_view(), name='boissonbar_update'),
    path('bar/boissons/<int:pk>/supprimer/', views.BoissonBarDeleteView.as_view(), name='boissonbar_delete'),

    # Bar - Catégories
    path('bar/categories/', views.CategorieBarListView.as_view(), name='categoriebar_list'),
    path('bar/categories/ajouter/', views.CategorieBarCreateView.as_view(), name='categoriebar_create'),
    path('bar/categories/<int:pk>/modifier/', views.CategorieBarUpdateView.as_view(), name='categoriebar_update'),
    path('bar/categories/<int:pk>/supprimer/', views.CategorieBarDeleteView.as_view(), name='categoriebar_delete'),

    # Bar - Tables (Cave)
    path('bar/tables/', views.TableBarListView.as_view(), name='tablebar_list'),
    path('bar/tables/ajouter/', views.TableBarCreateView.as_view(), name='tablebar_create'),
    path('bar/tables/<int:pk>/modifier/', views.TableBarUpdateView.as_view(), name='tablebar_update'),
    path('bar/tables/<int:pk>/supprimer/', views.TableBarDeleteView.as_view(), name='tablebar_delete'),

    # Restaurant - Tables
    path('tables/', views.TableListView.as_view(), name='table_list'),
    path('tables/ajouter/', views.TableCreateView.as_view(), name='table_create'),
    path('tables/<int:pk>/modifier/', views.TableUpdateView.as_view(), name='table_update'),
    path('tables/<int:pk>/supprimer/', views.TableDeleteView.as_view(), name='table_delete'),
    
    # Restaurant - Catégories
    path('categories/', views.CategorieListView.as_view(), name='categorie_list'),
    path('categories/ajouter/', views.CategorieCreateView.as_view(), name='categorie_create'),
    path('categories/<int:pk>/modifier/', views.CategorieUpdateView.as_view(), name='categorie_update'),
    path('categories/<int:pk>/supprimer/', views.CategorieDeleteView.as_view(), name='categorie_delete'),
    
    # Restaurant - Plats
    path('plats/', views.PlatListView.as_view(), name='plat_list'),
    path('plats/ajouter/', views.PlatCreateView.as_view(), name='plat_create'),
    path('plats/<int:pk>/modifier/', views.PlatUpdateView.as_view(), name='plat_update'),
    path('plats/<int:pk>/supprimer/', views.PlatDeleteView.as_view(), name='plat_delete'),
    
    # Espaces
    path('espaces/', views.EspaceListView.as_view(), name='espace_list'),
    path('espaces/ajouter/', views.EspaceCreateView.as_view(), name='espace_create'),
    path('espaces/<int:pk>/modifier/', views.EspaceUpdateView.as_view(), name='espace_update'),
    path('espaces/<int:pk>/supprimer/', views.EspaceDeleteView.as_view(), name='espace_delete'),
]