"""
Ajoute un print de debug dans restaurant_tpe
pour prouver quelle version du code s'execute
"""
VIEWS_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\restaurant\views.py"

with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
    contenu = f.read()

# Ajouter un print juste apres "boissons_bar = BoissonBar..."
ancien = '    for b in boissons_bar:\n        b.stock_quantity = int(b.quantite_stock)'
nouveau = '    print(f"DEBUG TPE: boissons={boissons_bar.count()} cats={categories_bar.count()}")\n    for b in boissons_bar:\n        b.stock_quantity = int(b.quantite_stock)'

if ancien in contenu:
    contenu = contenu.replace(ancien, nouveau, 1)
    with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print("Print ajoute — relancez le serveur et rechargez la page")
    print("Regardez la console du serveur Django")
else:
    print("Texte non trouve — voici les lignes 764-766:")
    for i, line in enumerate(contenu.splitlines()[762:768], 763):
        print(f"L{i}: {repr(line)}")
