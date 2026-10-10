@echo off
chcp 65001 >nul
pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "run.ps1" %*
set RC=%ERRORLEVEL%
popd
exit /b %RC%
