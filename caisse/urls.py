from django.urls import path
from . import views

app_name = 'caisse'

urlpatterns = [
    path('', views.index, name='index'),
    path('fermer/', views.fermer_caisse, name='fermer_caisse'),
]
