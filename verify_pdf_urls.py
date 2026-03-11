import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from facturation.views import facture_pdf, ticket_pdf, avoir_pdf, proforma_pdf
from facturation.models import Facture, Ticket, Avoir, Proforma
from django.contrib.auth.models import User

def verify_pdfs():
    factory = RequestFactory()
    user = User.objects.first()
    if not user:
        print("No user found!")
        return

    print("--- Verifying PDF Generation Views ---")

    # 1. Facture PDF
    facture = Facture.objects.last()
    if facture:
        print(f"Testing Facture PDF for #{facture.numero}...")
        request = factory.get(f'/facturation/factures/{facture.pk}/pdf/')
        request.user = user
        try:
            response = facture_pdf(request, pk=facture.pk)
            if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
                print("✅ Facture PDF OK")
            else:
                print(f"❌ Facture PDF Failed: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Facture PDF Error: {e}")
    else:
        print("⚠️ No Facture found to test.")

    # 2. Ticket PDF
    ticket = Ticket.objects.last()
    if ticket:
        print(f"Testing Ticket PDF for #{ticket.numero}...")
        request = factory.get(f'/facturation/tickets/{ticket.pk}/pdf/')
        request.user = user
        try:
            response = ticket_pdf(request, pk=ticket.pk)
            if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
                print("✅ Ticket PDF OK")
            else:
                print(f"❌ Ticket PDF Failed: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Ticket PDF Error: {e}")
    else:
        print("⚠️ No Ticket found to test.")

    # 3. Avoir PDF
    avoir = Avoir.objects.last()
    if avoir:
        print(f"Testing Avoir PDF for #{avoir.numero}...")
        request = factory.get(f'/facturation/avoirs/{avoir.pk}/pdf/')
        request.user = user
        try:
            response = avoir_pdf(request, pk=avoir.pk)
            if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
                print("✅ Avoir PDF OK")
            else:
                print(f"❌ Avoir PDF Failed: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Avoir PDF Error: {e}")
    else:
        print("⚠️ No Avoir found to test.")

    # 4. Proforma PDF
    proforma = Proforma.objects.last()
    if proforma:
        print(f"Testing Proforma PDF for #{proforma.numero}...")
        request = factory.get(f'/facturation/proformas/{proforma.pk}/pdf/')
        request.user = user
        try:
            response = proforma_pdf(request, pk=proforma.pk)
            if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
                print("✅ Proforma PDF OK")
            else:
                print(f"❌ Proforma PDF Failed: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Proforma PDF Error: {e}")
    else:
        print("⚠️ No Proforma found to test.")

if __name__ == "__main__":
    verify_pdfs()
