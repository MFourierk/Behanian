import os, re, io, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from django.core.management import call_command

buf = io.StringIO()
call_command('dumpdata',
    'cuisine.Fournisseur', 'cuisine.CategorieIngredient',
    'cuisine.UniteIngredient', 'cuisine.Ingredient',
    'cuisine.CategoriePlat', 'cuisine.FicheTechnique',
    'cuisine.LigneFicheTechnique', 'cuisine.Plat',
    indent=2, stdout=buf)

content = buf.getvalue()
content = re.sub(r'"cree_par": \d+', '"cree_par": null', content)

with open('cuisine_bundle.json', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

# Vérifications
with open('cuisine_bundle.json', 'rb') as f:
    b = f.read(3)
bom = 'OUI' if b == b'\xef\xbb\xbf' else 'NON'

data = json.loads(content)
noms = [o['fields'].get('nom', '') for o in data if 'nom' in o.get('fields', {})]

print(f"Objets: {len(data)}")
print(f"BOM: {bom}")
print(f"Exemples noms: {[n for n in noms if n][:6]}")
