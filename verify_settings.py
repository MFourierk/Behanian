
import os
import django
from django.conf import settings
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print(f"LOGIN_URL: {settings.LOGIN_URL}")
print(f"LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"LOGOUT_REDIRECT_URL: {settings.LOGOUT_REDIRECT_URL}")

try:
    login_url = reverse(settings.LOGIN_URL)
    print(f"Resolved LOGIN_URL ('{settings.LOGIN_URL}'): {login_url}")
except Exception as e:
    print(f"Error resolving LOGIN_URL: {e}")

try:
    dashboard_url = reverse('dashboard:index')
    print(f"Resolved dashboard:index: {dashboard_url}")
except Exception as e:
    print(f"Error resolving dashboard:index: {e}")
