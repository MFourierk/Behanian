from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('direction/', views.direction_view, name='direction'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
