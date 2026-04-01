from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='home'),
    path('users/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('hotel/', include('hotel.urls')),
    path('restaurant/', include('restaurant.urls')),
    path('bar/', include('bar.urls')),
    path('piscine/', include('piscine.urls')),
    path('boite-nuit/', include('boite_nuit.urls')),
    path('espaces-evenementiels/', include('espaces_evenementiels.urls')),
    path('rapport/', include('rapport.urls')),
    path('cuisine/', include('cuisine.urls')),
    path('caisse/', include('caisse.urls')),
    path('facturation/', include('facturation.urls')),
    path('parametres/', include('parametres.urls')),
]

# ── Remise à Zéro Admin (superuser uniquement) ──────────────────────────────
from dashboard.admin_reset_views import (
    reset_dashboard, reset_confirm, reset_execute, reset_success
)
urlpatterns += [
    path('admin/reset/', reset_dashboard, name='admin_reset_dashboard'),
    path('admin/reset/<str:type_reset>/confirm/', reset_confirm, name='admin_reset_confirm'),
    path('admin/reset/<str:type_reset>/execute/', reset_execute, name='admin_reset_execute'),
    path('admin/reset/<str:type_reset>/success/', reset_success, name='admin_reset_success'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
