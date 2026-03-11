from django.urls import path
from . import views

app_name = 'espaces_evenementiels'

urlpatterns = [
    path('', views.espaces_index, name='index'),
]