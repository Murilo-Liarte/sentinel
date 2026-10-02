# build_installer.ps1 - Automated Build & Packaging Pipeline for Sentinel
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  SENTINEL - Windows Installer and Distribution Builder " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Locate Python 3.11 Runtime
$PythonExe = Join-Path $ScriptDir ".python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) { $PythonExe = $cmd.Source }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found! Make sure .python311 exists."
    exit 1
}
Write-Host "[1/4] Using Python: $PythonExe" -ForegroundColor Green

# 2. Locate Inno Setup Compiler (ISCC.exe)
$IsccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\iscc.exe",
    "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
    "C:\Program Files\Inno Setup 6\iscc.exe"
)
$IsccExe = $null
foreach ($cand in $IsccCandidates) {
    if (Test-Path $cand) {
        $IsccExe = $cand
        break
    }
}
if (-not $IsccExe) {
    $cmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($cmd) { $IsccExe = $cmd.Source }
}

if (-not $IsccExe) {
    Write-Error "Inno Setup Compiler (iscc.exe) not found! Install it with: winget install JRSoftware.InnoSetup"
    exit 1
}
Write-Host "[2/4] Using Inno Setup Compiler: $IsccExe" -ForegroundColor Green

# 3. Compile Standalone Sentinel.exe via PyInstaller
Write-Host ""
Write-Host "[3/4] Compiling Sentinel.exe with PyInstaller..." -ForegroundColor Yellow
$pyArgs = @("-m", "PyInstaller", "Sentinel.spec", "--noconfirm")
$proc = Start-Process -FilePath $PythonExe -ArgumentList $pyArgs -Wait -PassThru -NoNewWindow
if ($proc.ExitCode -ne 0) {
    Write-Error "PyInstaller build failed with exit code $($proc.ExitCode)!"
    exit $proc.ExitCode
}

$ExePath = Join-Path $ScriptDir "dist\Sentinel.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "dist\Sentinel.exe was not produced!"
    exit 1
}
$ExeItem = Get-Item $ExePath
$ExeSizeMB = [math]::Round(($ExeItem.Length / 1MB), 2)
Write-Host "      Sentinel.exe compiled successfully ($ExeSizeMB MB)" -ForegroundColor Green

# 4. Compile Inno Setup Installer (dist\Sentinel-Setup.exe)
Write-Host ""
Write-Host "[4/4] Compiling Windows Setup Wizard with Inno Setup..." -ForegroundColor Yellow
$issPath = Join-Path $ScriptDir "Sentinel.iss"
$procInno = Start-Process -FilePath $IsccExe -ArgumentList @("`"$issPath`"") -Wait -PassThru -NoNewWindow
if ($procInno.ExitCode -ne 0) {
    Write-Error "Inno Setup compilation failed with exit code $($procInno.ExitCode)!"
    exit $procInno.ExitCode
}

$SetupPath = Join-Path $ScriptDir "dist\Sentinel-Setup.exe"
if (-not (Test-Path $SetupPath)) {
    Write-Error "dist\Sentinel-Setup.exe was not produced!"
    exit 1
}
$SetupItem = Get-Item $SetupPath
$SetupSizeMB = [math]::Round(($SetupItem.Length / 1MB), 2)
$SetupHash = (Get-FileHash -Path $SetupPath -Algorithm SHA256).Hash

# Copy version.json to dist
$VersionJson = Join-Path $ScriptDir "version.json"
$DistVersionJson = Join-Path $ScriptDir "dist\version.json"
if (Test-Path $VersionJson) {
    Copy-Item $VersionJson -Destination $DistVersionJson -Force
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE - DISTRIBUTION ASSETS READY" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Standalone Binary : $ExePath ($ExeSizeMB MB)" -ForegroundColor White
Write-Host "Setup Wizard      : $SetupPath ($SetupSizeMB MB)" -ForegroundColor White
Write-Host "Setup SHA256      : $SetupHash" -ForegroundColor DarkGray
Write-Host "Release Manifest  : $DistVersionJson" -ForegroundColor White
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
