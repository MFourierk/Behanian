from django.urls import path
from . import views

app_name = 'espaces_evenementiels'

urlpatterns = [
    path('', views.espaces_index, name='index'),
    path('api/reserver/', views.api_reserver, name='api_reserver'),
    path('api/encaisser/<int:reservation_id>/', views.api_encaisser, name='api_encaisser'),
    path('api/annuler/<int:reservation_id>/', views.api_annuler, name='api_annuler'),
    path('api/calendrier/', views.api_calendrier, name='api_calendrier'),
    path('api/espace/<int:espace_id>/', views.api_espace_detail, name='api_espace_detail'),
    path('recu/<int:reservation_id>/', views.recu_reservation, name='recu_reservation'),
]
