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
    path('cuisine/', include('cuisine.urls')),
    path('caisse/', include('caisse.urls')),
    path('facturation/', include('facturation.urls')),
    path('parametres/', include('parametres.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
