from django.urls import path
from . import views

app_name = 'hotel'

urlpatterns = [
    path('', views.hotel_index, name='index'),
    path('api/revenus/', views.api_revenus, name='api_revenus'),
    path('chambre/<int:chambre_id>/', views.chambre_detail, name='chambre_detail'),
    path('checkin/<int:reservation_id>/', views.checkin_reservation, name='checkin_reservation'),
    path('checkin/direct/', views.checkin_direct, name='checkin_direct'),
    path('reservation/create/', views.reservation_create, name='reservation_create'),
    path('checkin/print/<int:reservation_id>/', views.print_checkin_form, name='print_checkin_form'),
    path('checkout/<int:reservation_id>/', views.checkout_reservation, name='checkout_reservation'),
    path('checkout/finalize/<int:ticket_id>/', views.finalize_checkout, name='finalize_checkout'),
    path('consommation/add/<int:reservation_id>/', views.ajouter_consommation, name='ajouter_consommation'),
    path('ticket/<int:ticket_id>/print/', views.ticket_print, name='ticket_print'),
    path('api/consommations/<int:reservation_id>/', views.api_consommations_reservation, name='api_consommations'),
    path('api/consommation/<int:conso_id>/modifier/', views.api_modifier_consommation, name='api_modifier_conso'),
    path('api/consommation/<int:conso_id>/supprimer/', views.api_supprimer_consommation, name='api_supprimer_conso'),
]
