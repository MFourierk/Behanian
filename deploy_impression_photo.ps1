# =============================================================
# DÉPLOIEMENT : Impression + PDF + Photo plat
# Complexe Behanian — Session 4
# =============================================================
# Exécuter depuis :
#   D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project
# =============================================================

$projet = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"
Set-Location $projet

Write-Host "=== DÉPLOIEMENT Impression + PDF + Photo ===" -ForegroundColor Cyan

# 1. Arrêter le serveur Django
Write-Host "[1/6] Arrêt du serveur Django..." -ForegroundColor Yellow
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. Créer le dossier composants si absent
Write-Host "[2/6] Vérification du dossier components..." -ForegroundColor Yellow
$componentsDir = "$projet\templates\components"
if (!(Test-Path $componentsDir)) {
    New-Item -ItemType Directory -Path $componentsDir -Force | Out-Null
    Write-Host "    Dossier créé : templates\components" -ForegroundColor Green
} else {
    Write-Host "    Dossier déjà existant." -ForegroundColor Green
}

# 3. Copier le composant print_buttons
Write-Host "[3/6] Composant print_buttons.html..." -ForegroundColor Yellow
# Note : ce composant est inclus directement dans les templates,
# mais vous pouvez aussi le copier ici pour usage futur dans d'autres modules
# Copy-Item "CHEMIN_SOURCE\print_buttons.html" "$componentsDir\print_buttons.html" -Force

# 4. Formulaire bon de commande (avec impression)
Write-Host "[4/6] Bon de Commande avec impression..." -ForegroundColor Yellow
Copy-Item "REMPLACER_PAR_CHEMIN_SOURCE\cuisine_bon_commande_form.html" `
          "$projet\templates\cuisine\bon_commande_form.html" -Force
Write-Host "    templates\cuisine\bon_commande_form.html" -ForegroundColor Green

# 5. Bon de réception (avec impression)
Write-Host "[5/6] Bon de Réception avec impression..." -ForegroundColor Yellow
Copy-Item "REMPLACER_PAR_CHEMIN_SOURCE\cuisine_bon_reception_form.html" `
          "$projet\templates\cuisine\bon_reception_form.html" -Force
Write-Host "    templates\cuisine\bon_reception_form.html" -ForegroundColor Green

# 6. Formulaire plat (avec upload photo)
Write-Host "[6/6] Formulaire Plat avec upload photo..." -ForegroundColor Yellow
Copy-Item "REMPLACER_PAR_CHEMIN_SOURCE\cuisine_plat_form.html" `
          "$projet\templates\cuisine\plat_form.html" -Force
Write-Host "    templates\cuisine\plat_form.html" -ForegroundColor Green

# 7. Vérification MEDIA settings
Write-Host ""
Write-Host "=== VÉRIFICATION SETTINGS.PY ===" -ForegroundColor Cyan
$settings = Get-Content "$projet\behanian\settings.py" -Raw 2>$null
if ($settings -match "MEDIA_ROOT") {
    Write-Host "MEDIA_ROOT déjà configuré." -ForegroundColor Green
} else {
    Write-Host "ATTENTION : MEDIA_ROOT manquant dans settings.py !" -ForegroundColor Red
    Write-Host "Ajoutez ceci à la fin de settings.py :" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "import os"
    Write-Host "MEDIA_URL = '/media/'"
    Write-Host "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')"
    Write-Host ""
}

# 8. Vérifier Pillow
Write-Host ""
Write-Host "=== VÉRIFICATION PILLOW ===" -ForegroundColor Cyan
$pip = pip show pillow 2>&1
if ($pip -match "Name: Pillow") {
    Write-Host "Pillow installé." -ForegroundColor Green
} else {
    Write-Host "Pillow non installé — installation..." -ForegroundColor Yellow
    pip install Pillow
}

# 9. Vider le cache Python
Write-Host ""
Write-Host "=== NETTOYAGE CACHE ===" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 10. Relancer le serveur
Write-Host ""
Write-Host "=== LANCEMENT SERVEUR ===" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projet'; python manage.py runserver"
Start-Sleep -Seconds 3
Write-Host ""
Write-Host "=== DÉPLOIEMENT TERMINÉ ===" -ForegroundColor Green
Write-Host ""
Write-Host "Testez :" -ForegroundColor White
Write-Host "  - Bon commande : http://127.0.0.1:8000/cuisine/commandes/nouveau/"
Write-Host "  - Bon réception : http://127.0.0.1:8000/cuisine/receptions/nouveau/"
Write-Host "  - Plat (avec photo) : http://127.0.0.1:8000/cuisine/plats/nouveau/"
