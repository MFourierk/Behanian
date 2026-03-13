$base = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"
$src  = $PSScriptRoot

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  DEPLOY FOURNISSEURS + FICHES TECHNIQUES   " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$copies = @{
    # Fournisseurs
    "cuisine_fournisseur_list.html"           = "templates\cuisine\fournisseur_list.html"
    "cuisine_fournisseur_form.html"           = "templates\cuisine\fournisseur_form.html"
    "cuisine_fournisseur_confirm_delete.html" = "templates\cuisine\fournisseur_confirm_delete.html"
    # Fiches Techniques
    "cuisine_fiche_list.html"                 = "templates\cuisine\fiche_list.html"
    "cuisine_fiche_form.html"                 = "templates\cuisine\fiche_form.html"
    "cuisine_fiche_confirm_delete.html"       = "templates\cuisine\fiche_confirm_delete.html"
}

foreach ($item in $copies.GetEnumerator()) {
    $srcPath = "$src\$($item.Key)"
    $dstPath = "$base\$($item.Value)"
    $dir = Split-Path $dstPath -Parent
    if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Test-Path $srcPath) {
        Copy-Item -Path $srcPath -Destination $dstPath -Force
        Write-Host "[OK] $($item.Value)" -ForegroundColor Green
    } else {
        Write-Host "[MANQUANT] $($item.Key)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  DEPLOY TERMINE !" -ForegroundColor Green
Write-Host ""
Write-Host "Redemarrer le serveur :" -ForegroundColor White
Write-Host "  Stop-Process -Name python -Force" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Yellow
Write-Host ""
