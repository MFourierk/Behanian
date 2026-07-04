from django.urls import path
from . import views

app_name = 'rapport'

urlpatterns = [
    path('stock/', views.rapport_stock, name='stock'),
    path('marges/', views.rapport_marges, name='marges'),
    path('marges/print/', views.rapport_marges_print, name='marges_print'),
]
