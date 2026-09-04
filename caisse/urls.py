from django.urls import path
from . import views

app_name = 'caisse'

urlpatterns = [
    path('', views.index, name='index'),
    path('ouvrir/', views.ouvrir_caisse, name='ouvrir'),
    path('cloturer/', views.cloturer_caisse, name='cloturer'),
    path('force-cloturer/<int:session_id>/', views.force_cloturer_caisse, name='force_cloturer'),
    path('mouvement/', views.enregistrer_mouvement, name='mouvement'),
    path('prelevement/', views.prelevement_banque, name='prelevement'),
    path('rapport/', views.rapport_caisse, name='rapport'),
    path('rapport/<int:session_id>/', views.rapport_caisse, name='rapport_session'),
    path('rapport/excel/', views.rapport_caisse_excel, name='rapport_excel'),
    path('rapport/<int:session_id>/excel/', views.rapport_caisse_excel, name='rapport_session_excel'),
    path('rapport/transactions/', views.rapport_transactions, name='rapport_transactions'),
    path('etat-journee/', views.etat_journee, name='etat_journee'),
    path('historique/', views.historique, name='historique'),
    path('sync/', views.sync_centrale, name='sync'),
    path('api/stats/', views.api_stats_jour, name='api_stats'),
    path('api/reconciliation/', views.api_reconciliation, name='api_reconciliation'),
    path('api/modifier-ticket/', views.api_modifier_ticket, name='api_modifier_ticket'),
    path('api/modifier-mouvement/', views.api_modifier_mouvement, name='api_modifier_mouvement'),
    path('api/supprimer-mouvement/', views.api_supprimer_mouvement, name='api_supprimer_mouvement'),
]
