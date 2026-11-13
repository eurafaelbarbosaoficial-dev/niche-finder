# Cria a tarefa "Niche Finder - Backup" (toda segunda-feira, 4h). Rodar uma vez:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Vaio\Documents\Niche Finder\producao\agendar-backup.ps1"
$pasta = Split-Path -Parent $PSScriptRoot
$acao = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$pasta\backup.bat`"" -WorkingDirectory $pasta
$gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 4am
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Niche Finder - Backup" -Action $acao -Trigger $gatilho -Settings $config -Description "Backup privado semanal (producao/backup.py)" -Force | Out-Null
Write-Host "Tarefa 'Niche Finder - Backup' criada: toda segunda-feira as 4h." -ForegroundColor Green
