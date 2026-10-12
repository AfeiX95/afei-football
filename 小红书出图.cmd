@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AFC Xiaohongshu Card Matrix

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo.
  echo [x] Python not found. Install Python 3 first.
  echo.
  pause
  exit /b 1
)

rem Cards are rendered by HTML + local Chrome (scripts/xhs_html.py).
rem Nothing to pip install. If Chrome is not found, edit CHROME_CANDIDATES there.
%PY% scripts\xhs_html.py --menu
echo.
pause
