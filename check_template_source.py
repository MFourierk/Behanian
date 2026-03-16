"""
Vérifie quel template Django charge réellement
"""
import os, sys

PROJECT = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"
sys.path.insert(0, PROJECT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings

print("=== TEMPLATE DIRS Django ===")
for engine in settings.TEMPLATES:
    print(f"Backend: {engine['BACKEND']}")
    print(f"DIRS: {engine.get('DIRS', [])}")
    opts = engine.get('OPTIONS', {})
    print(f"APP_DIRS: {engine.get('APP_DIRS', False)}")
    print()

print("=== Tous les index.html trouvés ===")
for root, dirs, files in os.walk(PROJECT):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'staticfiles']]
    for f in files:
        if f == 'index.html' and 'restaurant' in root:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime)
            print(f"  {path}")
            print(f"    Taille: {size} bytes | Modifié: {dt.strftime('%d/%m/%Y %H:%M:%S')}")

print()
print("=== Test render direct ===")
from django.template.loader import get_template
try:
    t = get_template('restaurant/index.html')
    print(f"Template chargé depuis: {t.origin.name}")
except Exception as e:
    print(f"Erreur: {e}")
