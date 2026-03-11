from django.urls import path
from . import views

app_name = 'piscine'

urlpatterns = [
    path('', views.piscine_index, name='index'),
]