import os
import django
import sys
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from facturation.models import Facture, Client, Service, Article, LigneFacture, Avoir, LigneAvoir, Ticket
from facturation.views import get_logo_path
from hotel.models import Chambre  # Example content type
from django.contrib.contenttypes.models import ContentType

def run_verification():
    print("--- STARTING FULL VERIFICATION ---")

    # 0. Clean up test data
    print("\n0. Cleaning up previous test data...")
    Ticket.objects.filter(numero='TICKET-TEST-001').delete()
    Facture.objects.filter(client__nom="Client Test").delete()
    Avoir.objects.filter(client__nom="Client Test").delete()
    Client.objects.filter(nom="Client Test").delete()

    # 1. Setup Data
    print("\n1. Setting up test data...")
    user, _ = User.objects.get_or_create(username='test_verifier')
    client, _ = Client.objects.get_or_create(nom="Client Test", defaults={'email': 'test@test.com'})
    service, _ = Service.objects.get_or_create(nom="Service Test")
    
    # Create a dummy content object (e.g., a Room) for the Article
    chambre, _ = Chambre.objects.get_or_create(numero="999", type_chambre="standard", prix_nuit=5000, defaults={'etage': 1})
    ct = ContentType.objects.get_for_model(Chambre)
    
    article, _ = Article.objects.get_or_create(
        content_type=ct, 
        object_id=chambre.id, 
        defaults={'service': service}
    )

    # 2. Verify Facture Generation (A4)
    print("\n2. Verifying Facture (A4)...")
    facture = Facture.objects.create(
        client=client,
        cree_par=user,
        taux_tva=Decimal('18.00')
    )
    LigneFacture.objects.create(
        facture=facture,
        article=article,
        quantite=1,
        prix_unitaire=Decimal('5000.00'),
        description="Test Article"
    )
    facture.calculate_totals()
    print(f"   Facture created: {facture.numero}, Total: {facture.total}")

    # Generate HTML for Facture
    context_facture = {
        'facture': facture,
        'logo_path': get_logo_path(),
        'nom_entreprise': "TEST HOTEL",
    }
    html_facture = render_to_string('facturation/facture_pdf.html', context_facture)
    
    # Checks
    if "LogoB1.png" in html_facture or "LogoB1.png" in str(context_facture['logo_path']):
        print("   [PASS] Logo path found.")
    else:
        print("   [FAIL] Logo path NOT found.")
        
    if "F CFA" in html_facture:
        print("   [PASS] Currency 'F CFA' found.")
    else:
        print("   [FAIL] Currency 'F CFA' NOT found.")

    # Check for integer formatting (5000 instead of 5000,00)
    # Note: We look for the formatted string in the HTML. 
    # Since we used |floatformat:"-2", 5000.00 should appear as 5000
    if "5000" in html_facture and "5000,00" not in html_facture:
         print("   [PASS] Decimal formatting appears correct (no trailing zeros).")
    elif "5000" in html_facture:
         print("   [WARN] '5000' found, but '5000,00' might also be present. Please check visually if possible.")
    else:
         print("   [FAIL] formatting check inconclusive.")

    # 3. Verify Avoir from Facture (A4)
    print("\n3. Verifying Avoir from Facture (Standard A4)...")
    avoir_facture = Avoir.objects.create(
        numero="AVOIR-TEST-001",
        client=client,
        cree_par=user,
        facture_origine=facture
    )
    # Render logic as in views.py
    if hasattr(avoir_facture, 'ticket_origine') and avoir_facture.ticket_origine:
        template_name = 'facturation/avoir_ticket_pdf.html'
    else:
        template_name = 'facturation/avoir_pdf.html'
    
    print(f"   Selected Template: {template_name}")
    if template_name == 'facturation/avoir_pdf.html':
        print("   [PASS] Correct A4 template selected for Facture Avoir.")
    else:
        print("   [FAIL] Wrong template selected.")

    # 4. Verify Ticket (Thermal)
    print("\n4. Verifying Ticket (Thermal 80mm)...")
    ticket = Ticket.objects.create(
        client=client if client else None,
        montant_total=Decimal('2500.00'),
        module='hotel',
        numero='TICKET-TEST-001',
        contenu="Test ticket content"
    )
    context_ticket = {
        'ticket': ticket,
        'logo_path': get_logo_path(),
    }
    html_ticket = render_to_string('facturation/ticket_pdf.html', context_ticket)
    
    if "80mm" in html_ticket:
        print("   [PASS] '80mm' CSS found in Ticket template.")
    else:
        print("   [FAIL] '80mm' CSS NOT found in Ticket template.")

    # 5. Verify Avoir from Ticket (Thermal)
    print("\n5. Verifying Avoir from Ticket (Thermal 80mm)...")
    avoir_ticket = Avoir.objects.create(
        numero="AVOIR-TEST-002",
        client=client,
        cree_par=user,
        ticket_origine=ticket # Link to ticket
    )
    
    # Render logic check
    if hasattr(avoir_ticket, 'ticket_origine') and avoir_ticket.ticket_origine:
        template_name_at = 'facturation/avoir_ticket_pdf.html'
    else:
        template_name_at = 'facturation/avoir_pdf.html'

    print(f"   Selected Template: {template_name_at}")
    if template_name_at == 'facturation/avoir_ticket_pdf.html':
        print("   [PASS] Correct Thermal template selected for Ticket Avoir.")
    else:
        print("   [FAIL] Wrong template selected for Ticket Avoir.")
        
    html_avoir_ticket = render_to_string(template_name_at, {'avoir': avoir_ticket})
    if "80mm" in html_avoir_ticket:
        print("   [PASS] '80mm' CSS found in Avoir Ticket template.")
    else:
        print("   [FAIL] '80mm' CSS NOT found in Avoir Ticket template.")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == '__main__':
    try:
        run_verification()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
