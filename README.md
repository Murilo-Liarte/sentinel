# Sentinel — Home Entry/Exit Biometric Tracker

A 100% offline, local desktop application for home entry/exit detection using a webcam, facial recognition, tripwire motion tracking, and emotion analysis.

Built for Windows with native PySide6, OpenCV, vectorized dlib embeddings, ONNX Runtime emotion inference, multilingual internationalization, and an in-app global auto-updater.

---

## Key Features

| Feature | Description |
|---|---|
| **Live Vision Pipeline** | Real-time annotated webcam feed with bounding boxes, confidence tags, and virtual tripwire overlay. |
| **Vectorized Face Search** | Instant matching against 10,000+ faces in **0.16 ms** via hardware-accelerated BLAS matrix dot-product. |
| **Virtual Tripwire** | Draggable crossing line (5%–95% height) that classifies ENTER vs. EXIT trajectories with centroid tracking. |
| **Emotion Inference** | Lightweight ONNX model classifies facial emotion on tripwire crossings without cloud dependencies. |
| **Multilingual Engine** | Dynamic runtime UI translation: **Português (Brasil)** default, **English**, and **Español** without restarting. |
| **Windows Setup Wizard** | Packaged with Inno Setup 6 (`Sentinel-Setup.exe`) for seamless non-admin user-level installation. |
| **Global Auto-Updater** | Built-in background update checker, release notes modal, real-time speed meter, and silent upgrade installer. |
| **Data Privacy** | All biometric embeddings and logs stay 100% local in SQLite. Zero cloud tracking. |

---

## Quick Start for Users

### Option 1: Windows Installer Wizard (Recommended)
Download **`Sentinel-Setup.exe`** from the [Releases](https://github.com/your-username/sentinel/releases) tab:
1. Run the installer wizard (available in Portuguese, English, or Spanish).
2. It installs directly into your user profile (`%LOCALAPPDATA%\Programs\Sentinel`) without needing Windows Administrator permissions.
3. Launch Sentinel from your Desktop or Start Menu.

### Option 2: Run from Source
```powershell
# Run the automated installer (installs Python 3.11 environment and all wheels automatically)
.\install.bat

# Launch Sentinel
.\Sentinel.bat
```

---

## Building the Installer & Executable

To compile the standalone `.exe` and the multilingual Windows Setup Wizard:

```powershell
.\build_installer.ps1
```

This single command builds:
1. `dist\Sentinel.exe` (Standalone portable application)
2. `dist\Sentinel-Setup.exe` (Windows Installation Wizard with desktop shortcuts & uninstaller)
3. `dist\version.json` (Release manifest for the auto-updater)

See [`RELEASE_GUIDE.md`](RELEASE_GUIDE.md) for step-by-step instructions on publishing releases to GitHub or private servers.

---

## Project Structure

```
sentinel/
├── main.py               # Main GUI application & event coordinator
├── camera_worker.py      # Background thread: camera capture, dlib recognition, tracking
├── database.py           # SQLite layer: vectorized matrix loader, compact float32 storage
├── tracker.py            # CentroidTracker & Tripwire crossing logic
├── emotion_detector.py   # ONNX Runtime emotion inference (ferplus)
├── i18n.py               # Multilingual engine (pt_BR, en_US, es_ES)
├── updater.py            # Asynchronous background auto-updater & download dialog
├── styles.qss            # Sleek dark theme stylesheet
├── sentinel.ico          # Application icon
├── Sentinel.spec         # PyInstaller single-file build specification
├── Sentinel.iss          # Inno Setup 6 multilingual installer script
├── build_installer.ps1   # Turnkey packaging automation script
├── RELEASE_GUIDE.md      # Developer guide for global updates
├── version.json          # Version & update manifest
└── requirements.txt      # Python dependencies
```

---

## Technical Specifications

### Face Recognition & Scalability
- **Embeddings:** 128-dimensional unit float32 vectors stored as compact 512-byte raw buffers in SQLite.
- **Search Complexity:** Pre-stacked 2D matrix $\mathbf{M} \in \mathbb{R}^{N \times 128}$ evaluated via matrix multiplication:
  $$\mathbf{s} = \mathbf{M} \cdot \mathbf{q}$$
  Computes 10,000 cosine similarities in under 0.2 ms on modern CPUs.
- **Thread Safety:** Enforced global `_DLIB_LOCK` prevents C++ detector memory collisions between capture and tracking threads.

### Storage Layout
- User database: `%LOCALAPPDATA%\Sentinel\sentinel.db` (never wiped or modified during updates)
- Thumbnail crops: `%LOCALAPPDATA%\Sentinel\crops\`

---

## License

MIT License — free for personal and commercial use.
