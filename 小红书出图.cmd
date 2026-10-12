@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AFC Xiaohongshu Card Matrix

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys, PIL" >nul 2>nul
if errorlevel 1 (
  echo.
  echo [x] Python or Pillow is missing.
  echo     Install Python 3 first; then run:  %PY% -m pip install pillow
  echo.
  pause
  exit /b 1
)

%PY% scripts\xhs_cards.py --menu
echo.
pause
