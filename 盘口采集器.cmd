@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AFC Odds Collector (sporttery.cn)

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo.
  echo [x] Python not found.
  echo     Install Python 3 from python.org and tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

%PY% scripts\odds_snapshot.py menu
echo.
pause
