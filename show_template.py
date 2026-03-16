"""
Affiche les sections boissons et serveurs du template local
"""
TEMPLATE_PATH = r"D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project\templates\restaurant\index.html"

with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lignes : {len(lines)}")
print()

# Chercher boissons_bar
print("=== Lignes contenant 'boissons_bar' ===")
for i, line in enumerate(lines, 1):
    if 'boissons_bar' in line:
        print(f"  L{i}: {line.rstrip()}")

print()
# Chercher categories_bar
print("=== Lignes contenant 'categories_bar' ===")
for i, line in enumerate(lines, 1):
    if 'categories_bar' in line:
        print(f"  L{i}: {line.rstrip()}")

print()
# Chercher serveurs dans le template
print("=== Lignes contenant 'serveurs' ===")
for i, line in enumerate(lines, 1):
    if 'serveurs' in line.lower() and 'for' in line.lower():
        print(f"  L{i}: {line.rstrip()}")

print()
# Afficher le bloc boissons complet
print("=== Bloc view-boissons (20 lignes autour) ===")
for i, line in enumerate(lines, 1):
    if 'view-boissons' in line:
        start = max(0, i-2)
        end = min(len(lines), i+25)
        for j in range(start, end):
            print(f"  L{j+1}: {lines[j].rstrip()}")
        break
