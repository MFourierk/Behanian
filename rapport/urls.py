from django.urls import path
from . import views

app_name = 'rapport'

urlpatterns = [
    path('stock/', views.rapport_stock, name='stock'),
]
