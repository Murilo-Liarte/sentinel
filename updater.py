"""
updater.py — Sentinel In-App Global Auto-Updater Engine
======================================================
Provides asynchronous background update checking, release notes parsing,
chunked file downloading with real-time speed calculation, and silent
Windows Inno Setup installer replacement.

Supports both:
  1. Standard custom JSON endpoint (`version.json`)
  2. GitHub Releases API (`/releases/latest`)
"""

import os
import sys
import json
import time
import logging
import tempfile
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Tuple

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QWidget, QMessageBox
)

import i18n
import database

logger = logging.getLogger("Sentinel.Updater")

APP_VERSION = "1.0.8"
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/Murilo-Liarte/sentinel/main/version.json"


def parse_version(ver_str: str) -> Tuple[int, ...]:
    """Parse version string like 'v1.2.3' or '1.0' into a tuple of integers."""
    clean = ver_str.strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer_version(remote: str, local: str) -> bool:
    """Return True if remote version is strictly newer than local version."""
    return parse_version(remote) > parse_version(local)


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str = ""
    release_date: str = ""
    mandatory: bool = False
    sha256: str = ""


class UpdateCheckWorker(QThread):
    """
    Background worker thread to query the remote endpoint for new releases.
    Never blocks the GUI or camera capture thread.
    """
    update_available = Signal(object)  # UpdateInfo
    up_to_date = Signal(str)           # current_version
    check_error = Signal(str)          # error_message

    def __init__(self, update_url: Optional[str] = None, parent=None):
        super().__init__(parent)
        db_url = database.get_setting("update_url", "").strip()
        self.update_url = update_url or db_url or DEFAULT_UPDATE_URL

    def run(self):
        logger.info("Checking for updates from: %s", self.update_url)
        try:
            req = urllib.request.Request(
                self.update_url,
                headers={"User-Agent": f"Sentinel-Updater/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            info = self._parse_payload(data)
            if not info or not info.download_url:
                self.check_error.emit("Invalid update manifest received.")
                return

            if is_newer_version(info.version, APP_VERSION):
                logger.info("Newer version available: %s (current: %s)", info.version, APP_VERSION)
                self.update_available.emit(info)
            else:
                logger.info("Sentinel is up to date (version %s).", APP_VERSION)
                self.up_to_date.emit(APP_VERSION)

        except urllib.error.URLError as e:
            logger.warning("Network error while checking for updates: %s", e)
            self.check_error.emit(str(e.reason if hasattr(e, 'reason') else e))
        except Exception as e:
            logger.exception("Failed to check for updates: %s", e)
            self.check_error.emit(str(e))

    def _parse_payload(self, data: dict) -> Optional[UpdateInfo]:
        # Handle GitHub Releases API format
        if "tag_name" in data and "assets" in data:
            ver = data.get("tag_name", "").lstrip("vV")
            notes = data.get("body", "")
            date = data.get("published_at", "")[:10]
            dl_url = ""
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if name.endswith(".exe") and ("setup" in name or "sentinel" in name):
                    dl_url = asset.get("browser_download_url", "")
                    break
            if not dl_url and data.get("assets"):
                dl_url = data["assets"][0].get("browser_download_url", "")
            return UpdateInfo(version=ver, download_url=dl_url, release_notes=notes, release_date=date)

        # Handle standard version.json format
        if "version" in data:
            return UpdateInfo(
                version=data.get("version", ""),
                download_url=data.get("download_url", ""),
                release_notes=data.get("release_notes", ""),
                release_date=data.get("release_date", ""),
                mandatory=bool(data.get("mandatory", False)),
                sha256=data.get("sha256", ""),
            )

        return None


class UpdateDownloadWorker(QThread):
    """
    Downloads installer file in the background with progress and speed reporting.
    """
    progress = Signal(int, str)         # percent (0-100), speed_str (e.g. "3.5 MB/s")
    download_finished = Signal(str)     # target file path
    download_error = Signal(str)        # error message

    def __init__(self, download_url: str, version: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.version = version
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        target_path = os.path.join(tempfile.gettempdir(), f"Sentinel-Setup-{self.version}.exe")
        logger.info("Downloading update from %s to %s", self.download_url, target_path)

        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"Sentinel-Updater/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = response.getheader('Content-Length')
                total_size = int(total_size) if total_size and total_size.isdigit() else 0

                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB
                start_time = time.time()
                last_update_time = start_time

                with open(target_path, 'wb') as out_file:
                    while True:
                        if self._is_cancelled:
                            logger.info("Update download cancelled by user.")
                            out_file.close()
                            if os.path.exists(target_path):
                                os.remove(target_path)
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        out_file.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update_time >= 0.2:
                            dt = now - start_time
                            speed_bps = downloaded / dt if dt > 0 else 0
                            speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"

                            percent = int((downloaded / total_size) * 100) if total_size > 0 else 50
                            self.progress.emit(min(99, percent), speed_str)
                            last_update_time = now

            self.progress.emit(100, "")
            logger.info("Update download completed: %s", target_path)
            self.download_finished.emit(target_path)

        except Exception as e:
            logger.exception("Error downloading update: %s", e)
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass
            self.download_error.emit(str(e))


def apply_update(installer_path: str, silent: bool = True) -> bool:
    """
    Executes the Inno Setup installer and terminates the current Sentinel application.
    When silent=True, applies update in the background with zero user intervention.
    """
    if not os.path.exists(installer_path):
        logger.error("Installer not found: %s", installer_path)
        return False

    args = [installer_path]
    if silent:
        args.extend(["/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"])

    # Sanitize environment: strip PyInstaller runtime temp dirs so child processes don't inherit them
    clean_env = os.environ.copy()
    clean_env.pop("_MEIPASS2", None)
    clean_env.pop("_MEIPASS", None)

    logger.info("Launching installer: %s", " ".join(args))
    try:
        subprocess.Popen(args, env=clean_env, close_fds=True)
        return True
    except Exception as e:
        logger.exception("Failed to launch installer: %s", e)
        return False


class UpdateDialog(QDialog):
    """
    Clean, dark-themed update dialog matching Sentinel's aesthetic.
    """
    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_worker: Optional[UpdateDownloadWorker] = None
        self.downloaded_installer_path: Optional[str] = None

        self.setWindowTitle(i18n.t("update_dialog_title"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(460, 360)
        self.resize(520, 420)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header Title
        title_label = QLabel(i18n.t("update_available_title"))
        title_label.setObjectName("sectionHeader")
        title_label.setStyleSheet("font-size: 17px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title_label)

        # Version Info Row
        info_row = QHBoxLayout()
        cur_lbl = QLabel(i18n.t("update_current_version", version=APP_VERSION))
        cur_lbl.setStyleSheet("color: #8892B0; font-size: 12px;")
        new_lbl = QLabel(i18n.t("update_new_version", version=self.update_info.version))
        new_lbl.setStyleSheet("color: #00FF88; font-size: 13px; font-weight: bold;")
        info_row.addWidget(cur_lbl)
        info_row.addStretch()
        info_row.addWidget(new_lbl)
        layout.addLayout(info_row)

        # Release Notes Label
        notes_label = QLabel(i18n.t("update_release_notes"))
        notes_label.setStyleSheet("color: #CBD5E1; font-weight: bold; font-size: 12px;")
        layout.addWidget(notes_label)

        # Release Notes Content
        self.notes_box = QTextEdit()
        self.notes_box.setReadOnly(True)
        self.notes_box.setPlainText(self.update_info.release_notes or "Bug fixes and performance improvements.")
        self.notes_box.setStyleSheet(
            "background-color: #0F172A; color: #E2E8F0; border: 1px solid #334155; border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.notes_box)

        # Progress Bar (hidden until download starts)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; }"
            "QProgressBar::chunk { background-color: #00FF88; border-radius: 3px; }"
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Button Row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton(i18n.t("update_cancel"))
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.btn_cancel)

        self.btn_action = QPushButton(i18n.t("update_btn_update"))
        self.btn_action.setObjectName("btnStart")
        self.btn_action.clicked.connect(self._on_action_clicked)
        btn_row.addWidget(self.btn_action)

        layout.addLayout(btn_row)

    def _on_action_clicked(self):
        if self.downloaded_installer_path:
            # Inform user before closing and applying silent update
            instruction = i18n.t("update_instruction_msg", version=self.update_info.version)
            QMessageBox.information(self, i18n.t("update_ready_title"), instruction)

            self.status_label.setText("Starting installer...")

            # Clean shutdown of camera and parent window to release file & hardware locks
            if self.parent():
                if hasattr(self.parent(), "_worker") and self.parent()._worker:
                    try:
                        self.parent()._worker.stop()
                        self.parent()._worker.wait(1000)
                    except Exception:
                        pass
                if hasattr(self.parent(), "close"):
                    self.parent().close()

            time.sleep(0.5)
            success = apply_update(self.downloaded_installer_path, silent=True)
            if success:
                QApplication.quit()
                sys.exit(0)
            else:
                self.status_label.setText(i18n.t("update_error_msg", error="Could not start installer."))
            return

        # Start Download
        self.btn_action.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText(i18n.t("update_downloading", percent=0, speed="0 MB/s"))

        self.download_worker = UpdateDownloadWorker(
            self.update_info.download_url,
            self.update_info.version,
            parent=self
        )
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.download_finished.connect(self._on_download_finished)
        self.download_worker.download_error.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_progress(self, percent: int, speed: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(i18n.t("update_downloading", percent=percent, speed=speed))

    def _on_download_finished(self, path: str):
        self.downloaded_installer_path = path
        self.progress_bar.setValue(100)
        self.status_label.setText(i18n.t("update_download_complete"))
        self.btn_action.setText(i18n.t("update_install_now"))
        self.btn_action.setEnabled(True)

    def _on_download_error(self, error: str):
        self.btn_action.setEnabled(True)
        self.btn_action.setText(i18n.t("update_btn_update"))
        self.status_label.setText(i18n.t("update_error_msg", error=error))

    def _on_cancel(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(1000)
        self.reject()

    def closeEvent(self, event):
        self._on_cancel()
        super().closeEvent(event)
