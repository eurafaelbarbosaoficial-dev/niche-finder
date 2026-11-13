# Cria SÓ a tarefa "Niche Finder - Pautas semanais" (domingo 3h). Rodar uma vez:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Vaio\Documents\Niche Finder\producao\agendar-semanal.ps1"
$pasta = Split-Path -Parent $PSScriptRoot
$acao = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$pasta\oculto.vbs`" semanal.bat" -WorkingDirectory $pasta
$gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Niche Finder - Pautas semanais" -Action $acao -Trigger $gatilho -Settings $config -Description "Mede pautas novas de cada canal (producao/semanal.py)" -Force | Out-Null
Write-Host "Tarefa 'Niche Finder - Pautas semanais' criada: todo domingo as 3h." -ForegroundColor Green
