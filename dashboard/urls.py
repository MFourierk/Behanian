from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('direction/', views.direction_view, name='direction'),
    path('direction/mouvements/print/', views.mouvements_print, name='mouvements_print'),
    path('direction/mouvements/excel/', views.mouvements_excel, name='mouvements_excel'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
