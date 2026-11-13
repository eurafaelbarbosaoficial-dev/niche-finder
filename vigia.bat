@echo off
cd /d "%~dp0"
if not exist estado mkdir estado
where py >nul 2>&1 && (set PY=py -3) || (set PY=python)
%PY% -I vigia.py >> estado\vigia.txt 2>&1
