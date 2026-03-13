$base = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"
$src  = $PSScriptRoot

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "  DEPLOY PLATS / CARTE        " -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

$copies = @{
    "cuisine_plat_list.html"           = "templates\cuisine\plat_list.html"
    "cuisine_plat_form.html"           = "templates\cuisine\plat_form.html"
    "cuisine_plat_confirm_delete.html" = "templates\cuisine\plat_confirm_delete.html"
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
Write-Host "  TERMINE !" -ForegroundColor Green
Write-Host ""
Write-Host "  Stop-Process -Name python -Force" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Yellow
Write-Host ""
