
import os
import django
import sys
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from facturation.models import Service
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

try:
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser('testadmin', 'a@a.com', 'pass')

    c = Client()
    c.force_login(user)

    service = Service.objects.first()
    if not service:
        service = Service.objects.create(nom='S', prix_unitaire=1000)

    ct = ContentType.objects.get_for_model(Service)

    data = {
        'client_name': 'TEST_ERR',
        'client_phone': '0000',
        'client_email': 'test@example.com',  # Ajout de l'email requis
        'date_creation': timezone.now().strftime('%Y-%m-%d'),
        'remise': '0', 
        'tva': '0',
        'articles-1-service': str(service.id),
        'articles-1-description': f'{ct.id}:{service.id}',
        'articles-1-quantity': '1', 
        'articles-1-price': '1000'
    }

    print('--- DIAGNOSTIC START ---')
    url = reverse('facturation:create_document', args=['facture'])
    response = c.post(url, data, HTTP_HOST='127.0.0.1:8000')
    print(f'Status: {response.status_code}')

    if response.status_code != 200:
        content = response.content.decode()
        # Try to find exception value
        ex_val = re.search(r'<pre class="exception_value">(.*?)</pre>', content, re.DOTALL)
        if ex_val:
            print(f'ERROR MSG: {ex_val.group(1).strip()}')
        else:
            print('Could not find error message in HTML. Printing start of content:')
            print(content[:500])
    else:
        print('Success!')

except Exception as e:
    print(f'Script Error: {e}')
    import traceback
    traceback.print_exc()

print('--- DIAGNOSTIC END ---')
