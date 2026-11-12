@echo off
rem Niche Finder: roda uma busca completa e publica o site no GitHub a cada 5 minutos durante a busca.
rem A tarefa do Windows "Niche Finder" chama este arquivo sozinha (o instalar.ps1 cria a tarefa).
cd /d "%~dp0"
if not exist estado mkdir estado
where py >nul 2>&1 && (set PY=py -3) || (set PY=python)
%PY% -I finder.py --publicar 5 >> estado\saida.txt 2>&1
