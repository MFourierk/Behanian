from django.urls import path
from . import views

app_name = 'caisse'

urlpatterns = [
    path('', views.index, name='index'),
    path('suivi/', views.suivi_caisse, name='suivi'),
]
