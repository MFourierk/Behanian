from django.urls import path
from . import views

app_name = 'boite_nuit'

urlpatterns = [
    path('', views.boite_nuit_index, name='index'),
]