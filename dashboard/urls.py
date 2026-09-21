from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('keep-alive/', views.keep_alive, name='keep_alive'),
    path('direction/', views.direction_view, name='direction'),
    path('direction/mouvements/print/', views.mouvements_print, name='mouvements_print'),
    path('direction/mouvements/excel/', views.mouvements_excel, name='mouvements_excel'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('direction/resume-ventes/', views.resume_ventes_direction, name='resume_ventes'),
    path('direction/resume-ventes/api/', views.api_resume_ventes, name='api_resume_ventes'),
    path('direction/resume-ventes/excel/', views.resume_ventes_excel, name='resume_ventes_excel'),
    path('direction/resume-ventes/print/', views.resume_ventes_print, name='resume_ventes_print'),
    path('direction/stats-ventes/', views.stats_ventes, name='stats_ventes'),
    path('direction/stats-ventes/api/', views.api_stats_ventes, name='api_stats_ventes'),
    path('direction/stats-ventes/print/', views.stats_ventes_print, name='stats_ventes_print'),
]
