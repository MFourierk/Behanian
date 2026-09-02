# Behanian — Enregistrement de la tâche planifiée de backup
# Exécuter une fois en tant qu'Administrateur :
#   PowerShell -ExecutionPolicy Bypass -File register_backup_task.ps1

$TaskName   = "Behanian Backup Local"
$ScriptPath = Join-Path $PSScriptRoot "backup_local.py"
$Python     = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $Python) {
    Write-Error "Python introuvable dans le PATH. Installez Python puis relancez."
    exit 1
}

$Action   = New-ScheduledTaskAction -Execute $Python -Argument "`"$ScriptPath`""
$Trigger  = New-ScheduledTaskTrigger -Daily -At "03:00"
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit "00:30:00" `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName    $TaskName `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Description "Sauvegarde quotidienne Behanian VPS -> D:\.behanian\backups" `
    -RunLevel    Highest `
    -Force

Write-Host ""
Write-Host "Tâche '$TaskName' enregistrée — exécution chaque nuit à 03h00." -ForegroundColor Green
Write-Host "Backups dans : D:\.behanian\backups\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test immédiat : Start-ScheduledTask -TaskName '$TaskName'"
