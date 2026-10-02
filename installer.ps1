# ==============================================================================
#  installer.ps1 — Sentinel GUI Installer
#  Launched silently by install.bat — shows a proper Windows installation window.
#
#  Steps:
#    1. Detect Python 3.10+ (or install it silently via winget / direct download)
#    2. Create an isolated virtual environment (.venv)
#    3. Install dlib-bin (pre-compiled face recognition engine)
#    4. Install all remaining Python dependencies
#    5. Show success screen with a "Launch Sentinel" button
# ==============================================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── Palette (matches the app's dark theme) ────────────────────────────────────
$BG        = [System.Drawing.Color]::FromArgb(13,  17,  23)    # #0d1117
$SURFACE   = [System.Drawing.Color]::FromArgb(22,  27,  34)    # #161b22
$BORDER    = [System.Drawing.Color]::FromArgb(48,  54,  61)    # #30363d
$TEXT      = [System.Drawing.Color]::FromArgb(230, 237, 243)   # #e6edf3
$SUBTEXT   = [System.Drawing.Color]::FromArgb(139, 148, 158)   # #8b949e
$ACCENT    = [System.Drawing.Color]::FromArgb(31,  111, 235)   # #1f6feb
$SUCCESS   = [System.Drawing.Color]::FromArgb(35,  134, 54)    # #238636
$DANGER    = [System.Drawing.Color]::FromArgb(218, 54,  51)    # #da3633

# ── Fonts ─────────────────────────────────────────────────────────────────────
$FontTitle   = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$FontSub     = New-Object System.Drawing.Font("Segoe UI",  9)
$FontStep    = New-Object System.Drawing.Font("Segoe UI",  9, [System.Drawing.FontStyle]::Bold)
$FontBtn     = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$FontStatus  = New-Object System.Drawing.Font("Segoe UI",  8)
$FontMono    = New-Object System.Drawing.Font("Consolas",  8)

# ==============================================================================
#  BUILD THE FORM
# ==============================================================================
$form                   = New-Object System.Windows.Forms.Form
$form.Text              = "Sentinel Installer"
$form.Size              = New-Object System.Drawing.Size(560, 480)
$form.StartPosition     = "CenterScreen"
$form.FormBorderStyle   = "FixedSingle"
$form.MaximizeBox       = $false
$form.BackColor         = $BG
$form.ForeColor         = $TEXT

# ── Header panel ─────────────────────────────────────────────────────────────
$pnlHeader              = New-Object System.Windows.Forms.Panel
$pnlHeader.Size         = New-Object System.Drawing.Size(560, 90)
$pnlHeader.Location     = New-Object System.Drawing.Point(0, 0)
$pnlHeader.BackColor    = $SURFACE
$form.Controls.Add($pnlHeader)

$lblShield              = New-Object System.Windows.Forms.Label
$lblShield.Text         = "🛡"
$lblShield.Font         = New-Object System.Drawing.Font("Segoe UI Emoji", 28)
$lblShield.ForeColor    = $ACCENT
$lblShield.Location     = New-Object System.Drawing.Point(20, 18)
$lblShield.Size         = New-Object System.Drawing.Size(55, 55)
$pnlHeader.Controls.Add($lblShield)

$lblTitle               = New-Object System.Windows.Forms.Label
$lblTitle.Text          = "Sentinel"
$lblTitle.Font          = $FontTitle
$lblTitle.ForeColor     = $TEXT
$lblTitle.Location      = New-Object System.Drawing.Point(80, 15)
$lblTitle.Size          = New-Object System.Drawing.Size(440, 38)
$pnlHeader.Controls.Add($lblTitle)

$lblSubtitle            = New-Object System.Windows.Forms.Label
$lblSubtitle.Text       = "Home Entry / Exit Tracker — Setting up your application"
$lblSubtitle.Font       = $FontSub
$lblSubtitle.ForeColor  = $SUBTEXT
$lblSubtitle.Location   = New-Object System.Drawing.Point(82, 54)
$lblSubtitle.Size       = New-Object System.Drawing.Size(440, 20)
$pnlHeader.Controls.Add($lblSubtitle)

# ── Step indicators (5 rows) ──────────────────────────────────────────────────
$stepY = 108
$steps = @(
    "Checking for Python",
    "Installing Python 3.11",
    "Creating app environment",
    "Installing face recognition engine",
    "Installing remaining components"
)

$stepIcons   = @()
$stepLabels  = @()
$stepStatus  = @()

foreach ($i in 0..4) {
    $ico = New-Object System.Windows.Forms.Label
    $ico.Text      = "○"
    $ico.Font      = $FontStep
    $ico.ForeColor = $BORDER
    $ico.Location  = New-Object System.Drawing.Point(26, ($stepY + $i * 42))
    $ico.Size      = New-Object System.Drawing.Size(20, 22)
    $form.Controls.Add($ico)
    $stepIcons += $ico

    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text      = $steps[$i]
    $lbl.Font      = $FontSub
    $lbl.ForeColor = $SUBTEXT
    $lbl.Location  = New-Object System.Drawing.Point(52, ($stepY + $i * 42))
    $lbl.Size      = New-Object System.Drawing.Size(300, 20)
    $form.Controls.Add($lbl)
    $stepLabels += $lbl

    $st = New-Object System.Windows.Forms.Label
    $st.Text      = ""
    $st.Font      = $FontStatus
    $st.ForeColor = $SUBTEXT
    $st.Location  = New-Object System.Drawing.Point(52, ($stepY + $i * 42 + 18))
    $st.Size      = New-Object System.Drawing.Size(460, 18)
    $form.Controls.Add($st)
    $stepStatus += $st
}

# ── Progress bar ──────────────────────────────────────────────────────────────
$progressBar                = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location       = New-Object System.Drawing.Point(26, 328)
$progressBar.Size           = New-Object System.Drawing.Size(498, 14)
$progressBar.Minimum        = 0
$progressBar.Maximum        = 100
$progressBar.Value          = 0
$progressBar.Style          = "Continuous"
$progressBar.ForeColor      = $ACCENT
$form.Controls.Add($progressBar)

# ── Log box (scrollable detail) ───────────────────────────────────────────────
$logBox                     = New-Object System.Windows.Forms.RichTextBox
$logBox.Location            = New-Object System.Drawing.Point(26, 352)
$logBox.Size                = New-Object System.Drawing.Size(498, 60)
$logBox.BackColor           = $SURFACE
$logBox.ForeColor           = $SUBTEXT
$logBox.Font                = $FontMono
$logBox.ReadOnly            = $true
$logBox.BorderStyle         = "FixedSingle"
$logBox.ScrollBars          = "Vertical"
$form.Controls.Add($logBox)

# ── Bottom buttons ────────────────────────────────────────────────────────────
$btnLaunch                  = New-Object System.Windows.Forms.Button
$btnLaunch.Text             = "▶   Launch Sentinel"
$btnLaunch.Font             = $FontBtn
$btnLaunch.Location         = New-Object System.Drawing.Point(26, 424)
$btnLaunch.Size             = New-Object System.Drawing.Size(200, 36)
$btnLaunch.BackColor        = $SUCCESS
$btnLaunch.ForeColor        = [System.Drawing.Color]::White
$btnLaunch.FlatStyle        = "Flat"
$btnLaunch.FlatAppearance.BorderSize = 0
$btnLaunch.Enabled          = $false
$btnLaunch.Cursor           = [System.Windows.Forms.Cursors]::Hand
$btnLaunch.Add_Click({
    Start-Process -FilePath "$ScriptDir\.venv\Scripts\python.exe" `
                  -ArgumentList "`"$ScriptDir\main.py`"" `
                  -WindowStyle Hidden
    $form.Close()
})
$form.Controls.Add($btnLaunch)

$btnClose                   = New-Object System.Windows.Forms.Button
$btnClose.Text              = "Close"
$btnClose.Font              = $FontSub
$btnClose.Location          = New-Object System.Drawing.Point(240, 430)
$btnClose.Size              = New-Object System.Drawing.Size(80, 28)
$btnClose.BackColor         = $SURFACE
$btnClose.ForeColor         = $SUBTEXT
$btnClose.FlatStyle         = "Flat"
$btnClose.FlatAppearance.BorderColor = $BORDER
$btnClose.Add_Click({ $form.Close() })
$form.Controls.Add($btnClose)

# ── Helper functions (called from background thread via Invoke) ───────────────
function Update-Step {
    param([int]$idx, [string]$state, [string]$detail = "")
    # state: pending | running | done | error
    $form.Invoke([Action]{
        switch ($state) {
            "running" {
                $stepIcons[$idx].Text      = "◉"
                $stepIcons[$idx].ForeColor = $ACCENT
                $stepLabels[$idx].ForeColor = $TEXT
            }
            "done" {
                $stepIcons[$idx].Text      = "✓"
                $stepIcons[$idx].ForeColor = $SUCCESS
                $stepLabels[$idx].ForeColor = $TEXT
            }
            "skip" {
                $stepIcons[$idx].Text      = "✓"
                $stepIcons[$idx].ForeColor = $SUCCESS
                $stepLabels[$idx].ForeColor = $SUBTEXT
            }
            "error" {
                $stepIcons[$idx].Text      = "✗"
                $stepIcons[$idx].ForeColor = $DANGER
                $stepLabels[$idx].ForeColor = $DANGER
            }
        }
        if ($detail) { $stepStatus[$idx].Text = $detail }
    }) | Out-Null
}

function Set-Progress { param([int]$pct)
    $form.Invoke([Action]{ $progressBar.Value = [Math]::Min($pct, 100) }) | Out-Null
}

function Add-Log { param([string]$msg)
    $form.Invoke([Action]{
        $logBox.AppendText("$msg`n")
        $logBox.ScrollToCaret()
    }) | Out-Null
}

function Show-Success {
    $form.Invoke([Action]{
        $btnLaunch.Enabled = $true
        $lblSubtitle.Text  = "✅  Installation complete! Ready to launch."
        $lblSubtitle.ForeColor = $SUCCESS
    }) | Out-Null
}

function Show-Error { param([string]$msg)
    $form.Invoke([Action]{
        $lblSubtitle.Text      = "❌  Installation failed. See details below."
        $lblSubtitle.ForeColor = $DANGER
        $logBox.AppendText("`n[ERROR] $msg`n")
        $logBox.ScrollToCaret()
    }) | Out-Null
}

# ==============================================================================
#  INSTALLATION LOGIC  (runs on a background thread)
# ==============================================================================
function Find-Python {
    # Returns a python exe path for 3.10+ or $null
    $candidates = @("python", "python3", "py")
    foreach ($cmd in $candidates) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -ge 10) {
                    return (Get-Command $cmd -ErrorAction SilentlyContinue).Source
                }
            }
        } catch {}
    }
    # Also check common install paths
    $winPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($p in $winPaths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Install-PythonViaWinget {
    Add-Log "Trying winget (Windows Package Manager)..."
    $wg = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wg) { return $false }
    try {
        $proc = Start-Process winget -ArgumentList @(
            "install", "-e", "--id", "Python.Python.3.11",
            "--silent", "--accept-source-agreements",
            "--accept-package-agreements", "--scope", "user"
        ) -Wait -PassThru -WindowStyle Hidden
        if ($proc.ExitCode -eq 0) {
            # Refresh PATH in current session
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("PATH","User")
            Add-Log "Python installed via winget."
            return $true
        }
    } catch {}
    return $false
}

function Install-PythonViaDirect {
    Add-Log "Downloading Python 3.11 installer from python.org (~25 MB)..."
    $url  = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $dest = "$env:TEMP\python-3.11.9-amd64.exe"
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $dest)
        Add-Log "Download complete. Running Python installer silently..."
        $proc = Start-Process $dest -ArgumentList @(
            "/quiet", "InstallAllUsers=0", "PrependPath=1",
            "Include_test=0", "Include_doc=0", "Shortcuts=0"
        ) -Wait -PassThru
        Remove-Item $dest -Force -ErrorAction SilentlyContinue
        if ($proc.ExitCode -eq 0) {
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("PATH","User")
            Add-Log "Python 3.11 installed successfully."
            return $true
        }
        Add-Log ("Installer exit code: " + $proc.ExitCode)
        return $false
    } catch {
        Add-Log ("Download/install error: " + $_.Exception.Message)
        return $false
    }
}

function Run-Step {
    param([string]$exe, [string[]]$args)
    $psi             = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName    = $exe
    $psi.Arguments   = ($args | ForEach-Object { "`"$_`"" }) -join " "
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $out  = $proc.StandardOutput.ReadToEnd()
    $err  = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    if ($out.Trim()) { Add-Log $out.Trim() }
    if ($err.Trim()) { Add-Log $err.Trim() }
    return $proc.ExitCode
}

# ── Main installation sequence ────────────────────────────────────────────────
$installJob = [System.Threading.Thread]::new({

    try {
        # ── Step 0: Check / Install Python ──────────────────────────────────
        Update-Step 0 "running" "Searching for Python 3.10+..."
        Set-Progress 5

        $pythonExe = Find-Python

        if ($pythonExe) {
            $ver = (& $pythonExe --version 2>&1).ToString().Trim()
            Update-Step 0 "skip" "Found: $ver"
            Update-Step 1 "skip" "Python already installed — skipped"
            Add-Log "Using: $pythonExe ($ver)"
            Set-Progress 20
        } else {
            Update-Step 0 "done" "Python not found — installing now..."
            Update-Step 1 "running" "Downloading and installing Python 3.11..."
            Add-Log "Python 3.10+ not found. Beginning automatic install..."
            Set-Progress 8

            $ok = Install-PythonViaWinget
            if (-not $ok) { $ok = Install-PythonViaDirect }

            if (-not $ok) {
                Update-Step 1 "error" "Python installation failed"
                Show-Error ("Could not install Python automatically.`n" +
                            "Please install Python 3.11 from https://www.python.org/downloads/`n" +
                            "then double-click install.bat again.")
                return
            }

            # Re-locate after install
            $pythonExe = Find-Python
            if (-not $pythonExe) {
                # Last resort: well-known path after user-scope install
                $pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
            }

            $ver = (& $pythonExe --version 2>&1).ToString().Trim()
            Update-Step 1 "done" "Installed: $ver"
            Set-Progress 20
        }

        # ── Step 2: Create virtual environment ──────────────────────────────
        Update-Step 2 "running" "Creating isolated environment..."
        $venvDir = "$ScriptDir\.venv"

        if (Test-Path "$venvDir\Scripts\python.exe") {
            Update-Step 2 "skip" "Environment already exists — skipped"
            Add-Log "Existing .venv found — reusing."
        } else {
            $rc = Run-Step $pythonExe @("-m", "venv", $venvDir)
            if ($rc -ne 0) {
                Update-Step 2 "error" "Failed to create environment"
                Show-Error "Could not create virtual environment. Check disk space and permissions."
                return
            }
            Update-Step 2 "done" "Isolated environment ready"
        }
        Set-Progress 30

        $venvPip = "$venvDir\Scripts\pip.exe"

        # Upgrade pip silently
        Run-Step $pythonExe @("-m", "pip", "install", "--upgrade", "pip", "--quiet") | Out-Null

        # ── Step 3: dlib-bin ────────────────────────────────────────────────
        Update-Step 3 "running" "Installing dlib (this takes 1-3 minutes)..."
        Set-Progress 35
        Add-Log "Installing dlib-bin (pre-compiled face recognition engine)..."

        $rc = Run-Step $pythonExe @("-m", "pip", "install", "dlib-bin", "--quiet")
        if ($rc -ne 0) {
            Add-Log "dlib-bin failed — trying dlib..."
            $rc = Run-Step $pythonExe @("-m", "pip", "install", "dlib", "--quiet")
        }
        if ($rc -ne 0) {
            Update-Step 3 "error" "dlib installation failed"
            Show-Error ("Could not install the face recognition engine (dlib).`n" +
                        "Check your internet connection and try again.`n" +
                        "See README.md for manual installation steps.")
            return
        }
        Update-Step 3 "done" "Face recognition engine installed"
        Set-Progress 55

        # ── Step 4: remaining requirements ──────────────────────────────────
        Update-Step 4 "running" "Installing app components (3-6 minutes)..."
        Set-Progress 58
        Add-Log "Installing PySide6, OpenCV, face_recognition, deepface..."

        $reqFile = "$ScriptDir\requirements.txt"
        $rc = Run-Step $pythonExe @("-m", "pip", "install", "-r", $reqFile, "--quiet")
        if ($rc -ne 0) {
            Update-Step 4 "error" "Some packages failed to install"
            Show-Error ("Package installation failed. Check internet connection.`n" +
                        "Partial installation may still work — try launching Sentinel.")
            return
        }
        Update-Step 4 "done" "All components installed"
        Set-Progress 95

        # ── Finalise ────────────────────────────────────────────────────────
        # Ensure data directories exist
        New-Item -ItemType Directory -Force -Path "$ScriptDir\data\crops" | Out-Null
        Set-Progress 100

        Add-Log "`n✅ Installation complete!"
        Show-Success

    } catch {
        Add-Log ("Unexpected error: " + $_.Exception.Message)
        Show-Error $_.Exception.Message
    }
})

$installJob.IsBackground = $true
$installJob.Start()

# Show the window (blocks until form is closed)
[System.Windows.Forms.Application]::Run($form)
