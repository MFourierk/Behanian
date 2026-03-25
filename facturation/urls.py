from django.urls import path
from . import views

app_name = 'facturation'

urlpatterns = [
    path('receipt/depot/', views.receipt_depot, name='receipt_depot'),
    path('', views.index, name='index'),
    path('factures/', views.facture_list, name='facture_list'),
    path('factures/nouvelle/', views.facture_create, name='facture_create'),
    path('factures/<int:pk>/', views.facture_detail, name='facture_detail'),
    path('factures/<int:pk>/pdf/', views.facture_pdf, name='facture_pdf'),
    
    path('proformas/', views.proforma_list, name='proforma_list'),
    path('proformas/nouveau/', views.proforma_create, name='proforma_create'),
    path('proformas/<int:pk>/', views.proforma_detail, name='proforma_detail'),
    path('proformas/<int:pk>/pdf/', views.proforma_pdf, name='proforma_pdf'),
    path('proformas/<int:pk>/to-facture/', views.proforma_to_facture, name='proforma_to_facture'),
    
    path('avoirs/', views.avoir_list, name='avoir_list'),
    path('avoirs/nouveau/', views.avoir_create, name='avoir_create'),
    path('avoirs/<int:pk>/', views.avoir_detail, name='avoir_detail'),
    path('avoirs/<int:pk>/pdf/', views.avoir_pdf, name='avoir_pdf'),
    
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/create_avoir/', views.create_avoir_from_ticket, name='create_avoir_from_ticket'),
    path('tickets/<int:pk>/reprint/', views.ticket_reprint, name='ticket_reprint'),
    path('tickets/<int:pk>/thermal/', views.ticket_print_thermal, name='ticket_print_thermal'),
    path('tickets/<int:pk>/pdf/', views.ticket_pdf, name='ticket_pdf'),
    
    # API
    path('api/articles/<int:service_id>/', views.get_articles_by_service, name='get_articles_by_service'),
    path('api/document/<str:doc_type>/<int:pk>/', views.get_document_details, name='get_document_details'),
    path('api/client/<int:client_id>/', views.client_detail_api, name='client_detail_api'),
    path('api/create_document/<str:doc_type>/', views.create_document, name='create_document'),
]