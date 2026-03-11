from django.urls import path
from . import views

app_name = 'bar'

urlpatterns = [
    path('', views.bar_dashboard, name='dashboard'),
    path('commandes/', views.BonCommandeBarListView.as_view(), name='bon_commande_list'),
    path('stock/', views.stock_management, name='stock_management'),
]
