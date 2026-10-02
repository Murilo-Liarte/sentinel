# ==============================================================================
#  build.ps1 - Sentinel Build Pipeline
#  Compiles the entire application into a standalone Windows executable.
#
#  Usage:  Double-click build.bat  (or run this script directly)
#  Output: dist\Sentinel.exe
# ==============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "   Sentinel - Build Pipeline" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host ""

# -- Step 1: Locate Python --
Write-Host "[1/5] Locating Python..." -ForegroundColor Yellow

$embeddedPy = Join-Path $ScriptDir ".python311\python.exe"
if (Test-Path $embeddedPy) {
    $pythonExe = $embeddedPy
    $ver = (& $pythonExe --version 2>&1).ToString().Trim()
    Write-Host "  Using dedicated engine: $ver ($pythonExe)" -ForegroundColor Green
}
else {
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -eq 11) {
                    $pythonExe = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
                    Write-Host "  Found: $ver ($pythonExe)" -ForegroundColor Green
                    break
                }
            }
        } catch { }
    }
}

if (-not $pythonExe) {
    Write-Host "  ERROR: Python 3.10+ not found. Install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# -- Step 2: Create build virtual environment --
Write-Host "[2/5] Setting up build environment..." -ForegroundColor Yellow

$venvDir = Join-Path $ScriptDir ".buildenv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "  Build environment already exists - reusing." -ForegroundColor Green
}
else {
    Write-Host "  Creating isolated build environment..."
    & $pythonExe -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "  Created." -ForegroundColor Green
}

# -- Step 3: Install dependencies --
Write-Host "[3/5] Installing dependencies (this takes 3-8 minutes on first run)..." -ForegroundColor Yellow

# Upgrade pip
& $venvPython -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# Install dlib-bin first (pre-compiled)
Write-Host "  Installing dlib (face recognition engine)..."
& $venvPython -m pip install dlib-bin --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  dlib-bin failed, trying dlib from source..."
    & $venvPython -m pip install dlib --quiet 2>&1 | Out-Null
}

# Install project requirements
Write-Host "  Installing project requirements..."
$reqFile = Join-Path $ScriptDir "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Some packages failed. Check your internet connection." -ForegroundColor Red
    exit 1
}

# Install PyInstaller
Write-Host "  Installing PyInstaller..."
& $venvPython -m pip install pyinstaller --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to install PyInstaller." -ForegroundColor Red
    exit 1
}

Write-Host "  All dependencies ready." -ForegroundColor Green

# -- Step 4: Run PyInstaller --
Write-Host "[4/5] Building Sentinel.exe (this takes 2-5 minutes)..." -ForegroundColor Yellow
Write-Host "  Running PyInstaller with Sentinel.spec..." -ForegroundColor DarkGray

Push-Location $ScriptDir
& $venvPython -m PyInstaller Sentinel.spec --noconfirm --clean 2>&1 | ForEach-Object {
    $line = $_.ToString()
    if ($line -match "ERROR|error") {
        Write-Host "    $line" -ForegroundColor Red
    }
    elseif ($line -match "WARN|warning") {
        Write-Host "    $line" -ForegroundColor Yellow
    }
    else {
        Write-Host "    $line" -ForegroundColor DarkGray
    }
}
$buildResult = $LASTEXITCODE
Pop-Location

if ($buildResult -ne 0) {
    Write-Host ""
    Write-Host "  BUILD FAILED (exit code $buildResult)" -ForegroundColor Red
    Write-Host "  Check the output above for errors." -ForegroundColor Red
    exit 1
}

# -- Step 5: Report success --
$exePath = Join-Path $ScriptDir "dist\Sentinel.exe"
if (Test-Path $exePath) {
    $sizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  ==========================================" -ForegroundColor Green
    Write-Host "   BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "  ==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Output:  $exePath" -ForegroundColor White
    Write-Host "  Size:    $sizeMB MB" -ForegroundColor White
    Write-Host ""
    Write-Host "  This is a fully standalone .exe." -ForegroundColor Cyan
    Write-Host "  Copy it anywhere and double-click to run." -ForegroundColor Cyan
    Write-Host "  No Python or dependencies needed." -ForegroundColor Cyan
    Write-Host ""

    # Open the folder containing the exe
    Start-Process explorer.exe -ArgumentList "/select,`"$exePath`""
}
else {
    Write-Host ""
    Write-Host "  ERROR: Sentinel.exe was not produced." -ForegroundColor Red
    Write-Host "  Check the build output above for errors." -ForegroundColor Red
    exit 1
}
