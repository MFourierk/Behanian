from django.urls import path
from . import views

app_name = 'caisse'

urlpatterns = [
    path('', views.index, name='index'),
    path('ouvrir/', views.ouvrir_caisse, name='ouvrir'),
    path('cloturer/', views.cloturer_caisse, name='cloturer'),
    path('mouvement/', views.enregistrer_mouvement, name='mouvement'),
    path('prelevement/', views.prelevement_banque, name='prelevement'),
    path('rapport/', views.rapport_caisse, name='rapport'),
    path('rapport/<int:session_id>/', views.rapport_caisse, name='rapport_session'),
    path('historique/', views.historique, name='historique'),
    path('api/stats/', views.api_stats_jour, name='api_stats'),
]
