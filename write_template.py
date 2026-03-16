"""
Écrit directement le bon template restaurant/index.html
en remplaçant complètement l'ancien fichier
"""
import os
import urllib.request

DEST = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\templates\restaurant\index.html"
SRC  = r"C:\Users\mifok\Downloads\restaurant_index.html"

# Lire le fichier téléchargé
with open(SRC, 'r', encoding='utf-8') as f:
    contenu = f.read()

lignes = contenu.count('\n')
taille = len(contenu)

print(f"Fichier source : {lignes} lignes, {taille} bytes")

# Vérifications de base
checks = {
    'switchView':        'function switchView' in contenu,
    'ajouterBoisson':    'function ajouterBoisson' in contenu,
    'confirmerPaiement': 'function confirmerPaiement' in contenu,
    'nav-tab':           'nav-tab' in contenu,
    'boissons_bar':      'boissons_bar' in contenu,
    'endblock':          '{% endblock %}' in contenu,
}

print("\nVérifications :")
for k, v in checks.items():
    print(f"  {'OK' if v else 'MANQUANT'} — {k}")

if not all(checks.values()):
    print("\nERREUR : fichier source incomplet, abandon")
    exit(1)

# Backup
backup = DEST + '.before_final'
if os.path.exists(DEST):
    with open(DEST, 'r', encoding='utf-8') as f:
        old = f.read()
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(old)
    print(f"\nBackup : {backup}")

# Écriture
with open(DEST, 'w', encoding='utf-8', newline='\n') as f:
    f.write(contenu)

# Vérification finale
with open(DEST, 'r', encoding='utf-8') as f:
    verify = f.read()

if 'function switchView' in verify and len(verify) == taille:
    print(f"\n✅ SUCCÈS — {DEST}")
    print("→ Redémarrez le serveur Django")
    print("→ Ctrl+Shift+R dans le navigateur")
else:
    print("\n❌ ERREUR lors de l'écriture")
