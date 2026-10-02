# -*- mode: python ; coding: utf-8 -*-
"""
Sentinel.spec — PyInstaller build specification
=================================================
Bundles the entire Sentinel application into a single portable .exe:
  - Python runtime + all C extensions (dlib, cv2, PySide6)
  - face_recognition_models (dlib neural net weights)
  - styles.qss dark theme stylesheet
  - sentinel.ico app icon

Build with:   pyinstaller Sentinel.spec
Output:       dist/Sentinel.exe  (~150-250 MB)
"""

import os
import sys

# ── Locate face_recognition_models data files ──────────────────────────────────
# These are the pre-trained dlib .dat files (~100 MB) that face_recognition
# relies on for detection and encoding. They MUST be bundled.
try:
    import face_recognition_models
    face_models_dir = os.path.dirname(face_recognition_models.__file__)
    face_models_data = [
        (os.path.join(face_models_dir, 'models'), 'face_recognition_models/models'),
    ]
except ImportError:
    face_models_data = []
    print("WARNING: face_recognition_models not found — models won't be bundled.")

# ── Data files to include ──────────────────────────────────────────────────────
datas = [
    ('styles.qss', '.'),                 # QSS dark theme → root of bundle
    ('sentinel.ico', '.'),               # Icon for window
    ('models/emotion-ferplus-8.onnx', 'models'), # Emotion ONNX model
] + face_models_data

# ── Analysis ───────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Our modules (PyInstaller may miss them since they're imported dynamically)
        'app_paths',
        'database',
        'tracker',
        'camera_worker',
        'emotion_detector',
        'i18n',
        'updater',
        'pkg_resources',
        # scipy submodules used by face_recognition
        'scipy.spatial.transform._rotation_groups',
        'scipy.special.cython_special',
        # PySide6 plugins
        'PySide6.QtSvg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Strip out bloat we don't need
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    noarchive=False,
)

# ── Compile Python bytecode ────────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── Build single-file executable ───────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sentinel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # Compress with UPX if available
    console=False,               # ← NO terminal window — clean native GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sentinel.ico',         # App icon in taskbar & file explorer
)
