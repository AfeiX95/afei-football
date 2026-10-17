@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AFC Cards Publish Pack

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

rem Step 1: WebP publish version  (scripts/cards_post.py, PhotoCraft)
rem Step 2: multi-page PDF       (scripts/cards_pdf.py, PdfCraft / Pillow)
rem Usage: double-click = newest xhs batch; or drag a batch folder onto this file.

echo === 1/2  Publish version (WebP, PhotoCraft) ===
%PY% scripts\cards_post.py %*
if errorlevel 1 echo [x] WebP step reported a failure.
echo.
echo === 2/2  Combined PDF (PdfCraft) ===
%PY% scripts\cards_pdf.py %*
if errorlevel 1 echo [x] PDF step reported a failure.
echo.
pause
