# Niche Finder - prepara uma maquina nova (Windows) e cria a tarefa que roda a busca sozinha.
# Uso (PowerShell, dentro da pasta do Niche Finder):
#   powershell -ExecutionPolicy Bypass -File instalar.ps1            -> instala tudo e cria a tarefa (a cada 3 horas)
#   powershell -ExecutionPolicy Bypass -File instalar.ps1 -SemTarefa -> so instala, sem criar a tarefa
param([switch]$SemTarefa, [int]$Horas = 3, [int]$InicioMin = 2)
$ErrorActionPreference = "Continue"
$pasta = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $pasta

function Tem($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host "1/4 Python..."
if (-not (Tem "py") -and -not (Tem "python")) {
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Write-Host "   Python instalado. Feche e abra o PowerShell e rode este arquivo de novo." -ForegroundColor Yellow
    exit 1
}
$py = if (Tem "py") { "py" } else { "python" }

Write-Host "2/4 yt-dlp (le o YouTube)..."
& $py -m pip install -U --quiet yt-dlp

Write-Host "3/4 Deno (o yt-dlp precisa dele para o YouTube) e Git..."
if (-not (Tem "deno")) { winget install -e --id DenoLand.Deno --accept-source-agreements --accept-package-agreements }
if (-not (Tem "git"))  { winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements }

Write-Host "3b. Estudos de mercado (lupa da edição, skills do dono, memória do Claude)..."
$estudos = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "estudos-de-mercado"
if (-not (Test-Path $estudos)) {
    if (Tem "gh") { gh repo clone eurafaelbarbosaoficial-dev/estudos-de-mercado "$estudos" } else { Write-Host "   Falta o GitHub CLI (winget install GitHub.cli + gh auth login): clone depois o estudos-de-mercado." -ForegroundColor Yellow }
}
if (Test-Path "$estudos\setup\instalar.ps1") {
    & "$estudos\setup\instalar.ps1"   # watch-skill, ffmpeg, Demucs (a lupa)
    $sk = Join-Path $HOME ".claude\skills"; New-Item -ItemType Directory -Force $sk | Out-Null
    Get-ChildItem "$estudos\setup\skills" -Directory | ForEach-Object { if (-not (Test-Path "$sk\$($_.Name)")) { Copy-Item $_.FullName "$sk\$($_.Name)" -Recurse } }
    $mem = Join-Path $HOME ".claude\projects\C--Users-$env:USERNAME-Documents-Niche-Finder\memory"
    New-Item -ItemType Directory -Force $mem | Out-Null
    Copy-Item "$estudos\setup\memoria-claude\*.md" $mem -Force
    Write-Host "   skills e memoria do Claude restauradas." -ForegroundColor Green
}

if ($SemTarefa) { Write-Host "4/4 Tarefa do Windows: pulada (-SemTarefa)."; exit 0 }
Write-Host "4/4 Tarefa do Windows 'Niche Finder' (a cada $Horas horas)..."
$acao = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$pasta\oculto.vbs`" rodar.bat" -WorkingDirectory $pasta
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($InicioMin) -RepetitionInterval (New-TimeSpan -Hours $Horas)
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Niche Finder" -Action $acao -Trigger $gatilho -Settings $config -Description "Busca canais novos no YouTube e publica o site" -Force | Out-Null
Write-Host "   + Tarefa 'Niche Finder - Roteiros' (vigia dos pedidos de roteiro, a cada 10 min)..."
$acao2 = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$pasta\oculto.vbs`" vigia.bat" -WorkingDirectory $pasta
$gatilho2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($InicioMin) -RepetitionInterval (New-TimeSpan -Minutes 10)
$config2 = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Niche Finder - Roteiros" -Action $acao2 -Trigger $gatilho2 -Settings $config2 -Description "Escreve roteiros pedidos pelo botao do site" -Force | Out-Null
& (Join-Path $pasta "producao\agendar-semanal.ps1")
& (Join-Path $pasta "producao\agendar-backup.ps1")
Write-Host "Pronto. A primeira busca comeca em $InicioMin minutos." -ForegroundColor Green
Write-Host "Para o botao 'Fazer roteiro' funcionar: abra um terminal, rode 'claude' e faca /login uma vez." -ForegroundColor Yellow
