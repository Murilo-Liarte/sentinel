@echo off
:: ============================================================
::  Sentinel — Installer Entry Point
::  Double-click this file to install Sentinel.
::  This launches the graphical installer (no terminal needed).
:: ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0installer.ps1"
