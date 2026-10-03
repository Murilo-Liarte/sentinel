"""
settings_dialog.py — Sentinel Configuration & Preferences Dialog
================================================================
Provides a clean, dark/light-themed settings panel for:
  - Appearance & Theme (Dark Mode vs Light Day Mode)
  - Dynamic Language Selection (pt-BR, en-US, es-ES)
  - Camera Input Selection (System Default, USB, Secondary devices)
  - Camera FPS Target & Performance Tuning (15, 20, 30, 60 FPS)
  - Installed Application Version Display & Update Check
"""

import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QWidget,
    QTabWidget
)

import os
import database
import i18n
import updater
from app_paths import get_resource

logger = logging.getLogger("Sentinel.Settings")


class SettingsDialog(QDialog):
    """
    User settings modal for appearance, language, camera hardware, FPS, and version information.
    """
    settings_changed = Signal()

    def __init__(self, parent=None, on_check_updates_cb: Optional[Callable] = None, initial_tab: int = 0):
        super().__init__(parent)
        self._on_check_updates_cb = on_check_updates_cb

        self.setWindowTitle(i18n.t("settings_dialog_title"))
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(480, 420)
        self.resize(560, 500)

        icon_path = get_resource("sentinel.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self._load_current_values()
        self._apply_dialog_theme()

        if 0 <= initial_tab < self.tabs.count():
            self.tabs.setCurrentIndex(initial_tab)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # Tab Widget
        self.tabs = QTabWidget()

        # ── Tab 1: General & Appearance ───────────────────────────────────────
        tab_general = QWidget()
        layout_gen = QVBoxLayout(tab_general)
        layout_gen.setContentsMargins(16, 16, 16, 16)
        layout_gen.setSpacing(14)

        # 1. Appearance / Theme Box
        self.group_theme = QGroupBox(i18n.t("settings_theme_label"))
        box_theme_layout = QVBoxLayout(self.group_theme)
        self.lbl_theme_desc = QLabel(i18n.t("settings_theme_desc"))
        self.lbl_theme_desc.setObjectName("subtext")
        box_theme_layout.addWidget(self.lbl_theme_desc)

        self.theme_combo = QComboBox()
        self.theme_combo.setFixedHeight(32)
        self.theme_combo.addItem(i18n.t("theme_dark"), "dark")
        self.theme_combo.addItem(i18n.t("theme_light"), "light")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        box_theme_layout.addWidget(self.theme_combo)
        layout_gen.addWidget(self.group_theme)

        # 2. Language Box
        self.group_lang = QGroupBox(i18n.t("settings_lang_label"))
        box_lang_layout = QVBoxLayout(self.group_lang)
        self.lbl_lang_desc = QLabel(i18n.t("settings_lang_desc"))
        self.lbl_lang_desc.setObjectName("subtext")
        box_lang_layout.addWidget(self.lbl_lang_desc)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedHeight(32)
        for code, name in i18n.LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        box_lang_layout.addWidget(self.lang_combo)
        layout_gen.addWidget(self.group_lang)

        # 3. Version & Info Box
        self.group_ver = QGroupBox(i18n.t("settings_version_label"))
        box_ver_layout = QVBoxLayout(self.group_ver)
        self.lbl_version = QLabel(i18n.t("settings_version_info", version=updater.APP_VERSION))
        self.lbl_version.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold;")
        box_ver_layout.addWidget(self.lbl_version)

        self.lbl_engine = QLabel(i18n.t("settings_engine_info"))
        self.lbl_engine.setObjectName("subtext")
        box_ver_layout.addWidget(self.lbl_engine)

        self.btn_check_update = QPushButton(i18n.t("settings_btn_check_update"))
        self.btn_check_update.setFixedHeight(28)
        self.btn_check_update.clicked.connect(self._on_check_updates_clicked)
        box_ver_layout.addWidget(self.btn_check_update)
        layout_gen.addWidget(self.group_ver)

        layout_gen.addStretch()
        self.tabs.addTab(tab_general, i18n.t("settings_tab_general"))

        # ── Tab 2: Camera & Performance ───────────────────────────────────────
        tab_camera = QWidget()
        layout_cam = QVBoxLayout(tab_camera)
        layout_cam.setContentsMargins(16, 16, 16, 16)
        layout_cam.setSpacing(14)

        # 1. Camera Hardware Selection Box
        self.group_cam = QGroupBox(i18n.t("settings_cam_label"))
        box_cam_layout = QVBoxLayout(self.group_cam)
        self.lbl_cam_desc = QLabel(i18n.t("settings_cam_desc"))
        self.lbl_cam_desc.setObjectName("subtext")
        self.lbl_cam_desc.setWordWrap(True)
        box_cam_layout.addWidget(self.lbl_cam_desc)

        self.cam_combo = QComboBox()
        self.cam_combo.setFixedHeight(32)
        self.cam_combo.addItem(i18n.t("cam_device_0"), 0)
        self.cam_combo.addItem(i18n.t("cam_device_1"), 1)
        self.cam_combo.addItem(i18n.t("cam_device_2"), 2)
        self.cam_combo.addItem(i18n.t("cam_device_3"), 3)
        self.cam_combo.currentIndexChanged.connect(self._on_cam_changed)
        box_cam_layout.addWidget(self.cam_combo)
        layout_cam.addWidget(self.group_cam)

        # 2. FPS Control Box
        self.group_fps = QGroupBox(i18n.t("settings_fps_label"))
        box_fps_layout = QVBoxLayout(self.group_fps)
        self.lbl_fps_desc = QLabel(i18n.t("settings_fps_desc"))
        self.lbl_fps_desc.setWordWrap(True)
        self.lbl_fps_desc.setObjectName("subtext")
        box_fps_layout.addWidget(self.lbl_fps_desc)

        self.fps_combo = QComboBox()
        self.fps_combo.setFixedHeight(32)
        self.fps_combo.addItem("15 FPS (Baixo Consumo / Low CPU)", 15)
        self.fps_combo.addItem("20 FPS (Econômico / Balanced)", 20)
        self.fps_combo.addItem("30 FPS (Padrão Recomendado / Smooth)", 30)
        self.fps_combo.addItem("60 FPS (Alta Fluidez / High Performance)", 60)
        self.fps_combo.currentIndexChanged.connect(self._on_fps_changed)
        box_fps_layout.addWidget(self.fps_combo)
        layout_cam.addWidget(self.group_fps)

        layout_cam.addStretch()
        self.tabs.addTab(tab_camera, i18n.t("settings_tab_camera"))

        root.addWidget(self.tabs)

        # ── Bottom Button Bar ─────────────────────────────────────────────────
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_done = QPushButton(i18n.t("settings_btn_save"))
        self.btn_done.setObjectName("btn_success")
        self.btn_done.setFixedHeight(32)
        self.btn_done.clicked.connect(self.accept)
        btn_bar.addWidget(self.btn_done)

        root.addLayout(btn_bar)

    def _apply_dialog_theme(self):
        """Apply theme styling to the dialog components."""
        theme = database.get_setting("theme", "dark")
        if theme == "light":
            self.tabs.setStyleSheet(
                "QTabWidget::pane { border: 1px solid #CBD5E1; background-color: #FFFFFF; border-radius: 6px; } "
                "QTabBar::tab { background: #E2E8F0; color: #475569; padding: 8px 16px; margin-right: 4px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: 600; } "
                "QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-bottom: 2px solid #2563EB; }"
            )
            box_style = (
                "QGroupBox { font-weight: bold; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; margin-top: 10px; padding-top: 12px; } "
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            )
            btn_update_style = (
                "QPushButton { background-color: #F1F5F9; color: #2563EB; border: 1px solid #2563EB; border-radius: 4px; font-weight: 600; padding: 0 10px; } "
                "QPushButton:hover { background-color: #2563EB; color: #FFFFFF; }"
            )
        else:
            self.tabs.setStyleSheet(
                "QTabWidget::pane { border: 1px solid #334155; background-color: #0F172A; border-radius: 6px; } "
                "QTabBar::tab { background: #1E293B; color: #94A3B8; padding: 8px 16px; margin-right: 4px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: 600; } "
                "QTabBar::tab:selected { background: #0F172A; color: #10B981; border-bottom: 2px solid #10B981; }"
            )
            box_style = (
                "QGroupBox { font-weight: bold; color: #E2E8F0; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 12px; } "
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            )
            btn_update_style = (
                "QPushButton { background-color: #1E293B; color: #38BDF8; border: 1px solid #38BDF8; border-radius: 4px; font-weight: 600; padding: 0 10px; } "
                "QPushButton:hover { background-color: #38BDF8; color: #0F172A; }"
            )

        self.group_theme.setStyleSheet(box_style)
        self.group_lang.setStyleSheet(box_style)
        self.group_ver.setStyleSheet(box_style)
        self.group_cam.setStyleSheet(box_style)
        self.group_fps.setStyleSheet(box_style)
        self.btn_check_update.setStyleSheet(btn_update_style)

    def _load_current_values(self):
        # 1. Theme
        cur_theme = database.get_setting("theme", "dark")
        for idx in range(self.theme_combo.count()):
            if self.theme_combo.itemData(idx) == cur_theme:
                self.theme_combo.setCurrentIndex(idx)
                break

        # 2. Language
        cur_lang = i18n.get_language()
        for idx in range(self.lang_combo.count()):
            if self.lang_combo.itemData(idx) == cur_lang:
                self.lang_combo.setCurrentIndex(idx)
                break

        # 3. Camera Device
        try:
            cur_cam = int(database.get_setting("camera_index", "0"))
        except (ValueError, TypeError):
            cur_cam = 0
        for idx in range(self.cam_combo.count()):
            if self.cam_combo.itemData(idx) == cur_cam:
                self.cam_combo.setCurrentIndex(idx)
                break

        # 4. FPS
        try:
            cur_fps = int(database.get_setting("target_fps", "30"))
        except (ValueError, TypeError):
            cur_fps = 30
        for idx in range(self.fps_combo.count()):
            if self.fps_combo.itemData(idx) == cur_fps:
                self.fps_combo.setCurrentIndex(idx)
                break

    def _on_theme_changed(self, index: int):
        theme = self.theme_combo.itemData(index)
        if theme:
            database.set_setting("theme", theme)
            self._apply_dialog_theme()
            self.settings_changed.emit()

    def _on_lang_changed(self, index: int):
        code = self.lang_combo.itemData(index)
        if code and code != i18n.get_language():
            i18n.set_language(code)
            database.set_setting("language", code)
            self._retranslate_self()
            self.settings_changed.emit()

    def _on_cam_changed(self, index: int):
        cam_idx = self.cam_combo.itemData(index)
        if cam_idx is not None:
            database.set_setting("camera_index", str(cam_idx))
            self.settings_changed.emit()

    def _on_fps_changed(self, index: int):
        fps = self.fps_combo.itemData(index)
        if fps:
            database.set_setting("target_fps", str(fps))
            self.settings_changed.emit()

    def _on_check_updates_clicked(self):
        self.close()
        if self._on_check_updates_cb:
            self._on_check_updates_cb()

    def _retranslate_self(self):
        """Retranslate this dialog's labels dynamically."""
        self.setWindowTitle(i18n.t("settings_dialog_title"))
        self.tabs.setTabText(0, i18n.t("settings_tab_general"))
        self.tabs.setTabText(1, i18n.t("settings_tab_camera"))

        # Theme
        self.group_theme.setTitle(i18n.t("settings_theme_label"))
        self.lbl_theme_desc.setText(i18n.t("settings_theme_desc"))
        cur_theme_idx = self.theme_combo.currentIndex()
        self.theme_combo.blockSignals(True)
        self.theme_combo.setItemText(0, i18n.t("theme_dark"))
        self.theme_combo.setItemText(1, i18n.t("theme_light"))
        self.theme_combo.setCurrentIndex(cur_theme_idx)
        self.theme_combo.blockSignals(False)

        # Language
        self.group_lang.setTitle(i18n.t("settings_lang_label"))
        self.lbl_lang_desc.setText(i18n.t("settings_lang_desc"))

        # Version
        self.group_ver.setTitle(i18n.t("settings_version_label"))
        self.lbl_version.setText(i18n.t("settings_version_info", version=updater.APP_VERSION))
        self.lbl_engine.setText(i18n.t("settings_engine_info"))
        self.btn_check_update.setText(i18n.t("settings_btn_check_update"))

        # Camera
        self.group_cam.setTitle(i18n.t("settings_cam_label"))
        self.lbl_cam_desc.setText(i18n.t("settings_cam_desc"))
        cur_cam_idx = self.cam_combo.currentIndex()
        self.cam_combo.blockSignals(True)
        self.cam_combo.setItemText(0, i18n.t("cam_device_0"))
        self.cam_combo.setItemText(1, i18n.t("cam_device_1"))
        self.cam_combo.setItemText(2, i18n.t("cam_device_2"))
        self.cam_combo.setItemText(3, i18n.t("cam_device_3"))
        self.cam_combo.setCurrentIndex(cur_cam_idx)
        self.cam_combo.blockSignals(False)

        # FPS
        self.group_fps.setTitle(i18n.t("settings_fps_label"))
        self.lbl_fps_desc.setText(i18n.t("settings_fps_desc"))

        # Save button
        self.btn_done.setText(i18n.t("settings_btn_save"))
