from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.restaurant_index, name='index'),
    path('valider-commande/', views.valider_commande, name='valider_commande'),
    path('annuler-commande/', views.annuler_commande, name='annuler_commande'),
    path('recuperer-commande/<int:commande_id>/', views.recuperer_commande, name='recuperer_commande_details'),
    path('supprimer-ligne-commande/', views.supprimer_ligne_commande, name='supprimer_ligne_commande'),
    path('ajouter-item-commande/', views.ajouter_item_commande, name='ajouter_item_commande'),
    path('update-ligne-quantite/', views.update_ligne_quantite, name='update_ligne_quantite'),
    path('add-accompagnement-to-ligne/', views.add_accompagnement_to_ligne, name='add_accompagnement_to_ligne'),
    path('create-reservation/', views.create_reservation, name='create_reservation'),
    path('update-reservation-status/', views.update_reservation_status, name='update_reservation_status'),
]
