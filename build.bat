@echo off
:: ============================================================
::  Sentinel — Build Standalone .exe
::  Double-click this file to compile Sentinel into a portable
::  executable that runs without Python installed.
:: ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
pause
