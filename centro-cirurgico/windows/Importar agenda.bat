@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
title Importar agenda do centro cirurgico

set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :achou
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
:achou

if not defined PY (
  echo Python nao encontrado. Rode antes o "instalar_uma_vez.bat".
  echo.
  pause
  exit /b 1
)

echo Importando a agenda...
echo.
%PY% "%~dp0importar_agenda.py" --abrir %*
echo.
pause
