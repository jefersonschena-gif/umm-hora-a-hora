@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Instalacao - Importador da agenda

echo ==================================================
echo  Importador da agenda - instalacao (uma vez so)
echo ==================================================
echo.

set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :achou
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
:achou

if not defined PY (
  echo O Python ainda nao esta instalado neste computador.
  echo.
  echo   1^) Abra:  https://www.python.org/downloads/windows/
  echo   2^) Baixe o instalador do Python 3 para Windows
  echo   3^) Na PRIMEIRA tela, marque "Add python.exe to PATH"
  echo   4^) Conclua a instalacao e rode este arquivo de novo
  echo.
  pause
  exit /b 1
)

echo Python encontrado:
%PY% --version
echo.
echo Instalando os componentes (openpyxl e pypdf)...
echo.
%PY% -m pip install --upgrade openpyxl "pypdf[crypto]"
if not errorlevel 1 goto :pronto

echo.
echo Tentando de novo sem o componente opcional...
%PY% -m pip install --upgrade openpyxl pypdf
if errorlevel 1 (
  echo.
  echo Nao deu para instalar. Confira a conexao com a internet e tente de novo.
  pause
  exit /b 1
)
:pronto

echo.
echo ==================================================
echo  Pronto. Agora use o "Importar agenda.bat".
echo ==================================================
pause
