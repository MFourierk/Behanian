from django.urls import path
from . import views

app_name = 'espaces_evenementiels'

urlpatterns = [
    path('', views.espaces_index, name='index'),
    path('api/reserver/', views.api_reserver, name='api_reserver'),
    path('api/encaisser/<int:reservation_id>/', views.api_encaisser, name='api_encaisser'),
    path('api/espace/<int:espace_id>/', views.api_espace_detail, name='api_espace_detail'),
]
