$base = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"
$src  = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY TEMPLATES CUISINE + BREADCRUMB " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$copies = @{
    "breadcrumb.html"                 = "templates\components\breadcrumb.html"
    "cuisine_ingredient_form.html"    = "templates\cuisine\ingredient_form.html"
    "cuisine_bon_commande_form.html"  = "templates\cuisine\bon_commande_form.html"
    "cuisine_bon_reception_form.html" = "templates\cuisine\bon_reception_form.html"
    "cuisine_inventaire_form.html"    = "templates\cuisine\inventaire_form.html"
    "cuisine_casse_form.html"         = "templates\cuisine\casse_form.html"
    "cuisine_stock_management.html"   = "templates\cuisine\stock_management.html"
    "cuisine_index.html"              = "templates\cuisine\index.html"
}

foreach ($item in $copies.GetEnumerator()) {
    $srcPath = "$src\$($item.Key)"
    $dstPath = "$base\$($item.Value)"
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
