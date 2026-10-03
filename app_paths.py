"""
app_paths.py — Sentinel
========================
Centralized path resolver for both development and frozen .exe builds.

When running as a raw Python script:
    - Read-only resources (styles.qss) are relative to __file__
    - Writable data (sentinel.db, crops/) is in a local 'data/' folder

When frozen into a standalone .exe by PyInstaller:
    - Read-only resources live inside sys._MEIPASS (temp unpack directory)
    - Writable data persists in %LOCALAPPDATA%\\Sentinel\\
"""

import os
import sys


def is_frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def get_bundle_dir() -> str:
    """
    Return the read-only bundle directory.
    - Frozen:     sys._MEIPASS  (PyInstaller temp dir)
    - Dev:        directory containing this script
    """
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def get_resource(rel_path: str) -> str:
    """
    Get absolute path to a bundled read-only asset.
    Example: get_resource("styles.qss")
    """
    return os.path.join(get_bundle_dir(), rel_path)


def get_app_data_dir() -> str:
    """
    Return the persistent writable directory for user data.
    - Frozen:  %LOCALAPPDATA%\\Sentinel\\
    - Dev:     ./data/
    """
    if is_frozen():
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(base, "Sentinel")
    else:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path() -> str:
    """Persistent SQLite database location."""
    return os.path.join(get_app_data_dir(), "sentinel.db")


def get_crops_dir() -> str:
    """Persistent directory for face crop thumbnails."""
    crops = os.path.join(get_app_data_dir(), "crops")
    os.makedirs(crops, exist_ok=True)
    return crops


def get_avatars_dir() -> str:
    """Persistent directory for enrolled user portrait avatars."""
    avatars = os.path.join(get_app_data_dir(), "avatars")
    os.makedirs(avatars, exist_ok=True)
    return avatars

