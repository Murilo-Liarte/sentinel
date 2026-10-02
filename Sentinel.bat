@echo off
:: ============================================================
::  Sentinel — Launcher
::  Double-click this file anytime to open the app.
:: ============================================================

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    :: Not installed yet — offer to run the installer
    powershell -NoProfile -WindowStyle Hidden -Command ^
        "[System.Windows.Forms.MessageBox]::Show('Sentinel is not installed yet.`nPlease double-click install.bat first.','Sentinel','OK','Warning')" 2>nul
    echo Sentinel is not installed yet.
    echo Please double-click install.bat first.
    pause
    exit /b 1
)

:: Launch the app — hidden window, app has its own GUI
start "" "%VENV_PYTHON%" "%~dp0main.py"
