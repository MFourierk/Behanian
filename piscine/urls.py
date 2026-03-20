from django.urls import path
from . import views

app_name = 'piscine'

urlpatterns = [
    path('', views.piscine_index, name='index'),
    path('entree/', views.enregistrer_entree, name='entree'),
    path('consommation/<int:acces_id>/', views.ajouter_consommation, name='consommation'),
    path('sortie/<int:acces_id>/', views.encaisser_sortie, name='sortie'),
    path('tarifs/', views.configurer_tarifs, name='tarifs'),
    path('api/acces/<int:acces_id>/', views.api_acces_detail, name='acces_detail'),
    path('consommation/<int:conso_id>/modifier/', views.modifier_consommation, name='modifier_conso'),
    path('consommation/<int:conso_id>/supprimer/', views.supprimer_consommation, name='supprimer_conso'),
]
