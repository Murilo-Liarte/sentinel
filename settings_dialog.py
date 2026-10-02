"""
settings_dialog.py — Sentinel Configuration & Preferences Dialog
================================================================
Provides a clean, dark-themed settings panel for:
  - Dynamic Language Selection (pt-BR, en-US, es-ES)
  - Camera FPS Target & Performance Tuning (15, 20, 30, 60 FPS)
  - Installed Application Version Display & Update Check
"""

import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QWidget,
    QTabWidget, QSpinBox
)

import database
import i18n
import updater

logger = logging.getLogger("Sentinel.Settings")


class SettingsDialog(QDialog):
    """
    User settings modal for language, camera FPS, and version information.
    """
    settings_changed = Signal()

    def __init__(self, parent=None, on_check_updates_cb: Optional[Callable] = None):
        super().__init__(parent)
        self._on_check_updates_cb = on_check_updates_cb

        self.setWindowTitle(i18n.t("settings_dialog_title"))
        self.setFixedSize(520, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #334155; background-color: #0F172A; border-radius: 6px; } "
            "QTabBar::tab { background: #1E293B; color: #94A3B8; padding: 8px 16px; margin-right: 4px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: 600; } "
            "QTabBar::tab:selected { background: #0F172A; color: #00FF88; border-bottom: 2px solid #00FF88; }"
        )

        # ── Tab 1: General & Language ─────────────────────────────────────────
        tab_general = QWidget()
        layout_gen = QVBoxLayout(tab_general)
        layout_gen.setContentsMargins(16, 16, 16, 16)
        layout_gen.setSpacing(16)

        # Language Box
        self.group_lang = QGroupBox(i18n.t("settings_lang_label"))
        self.group_lang.setStyleSheet("QGroupBox { font-weight: bold; color: #E2E8F0; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
        box_lang_layout = QVBoxLayout(self.group_lang)

        self.lbl_lang_desc = QLabel(i18n.t("settings_lang_desc"))
        self.lbl_lang_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        box_lang_layout.addWidget(self.lbl_lang_desc)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedHeight(32)
        for code, name in i18n.LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        box_lang_layout.addWidget(self.lang_combo)

        layout_gen.addWidget(self.group_lang)

        # Version & Info Box
        self.group_ver = QGroupBox(i18n.t("settings_version_label"))
        self.group_ver.setStyleSheet("QGroupBox { font-weight: bold; color: #E2E8F0; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
        box_ver_layout = QVBoxLayout(self.group_ver)

        self.lbl_version = QLabel(i18n.t("settings_version_info", version=updater.APP_VERSION))
        self.lbl_version.setStyleSheet("color: #00FF88; font-size: 13px; font-weight: bold;")
        box_ver_layout.addWidget(self.lbl_version)

        self.lbl_engine = QLabel(i18n.t("settings_engine_info"))
        self.lbl_engine.setStyleSheet("color: #64748B; font-size: 11px;")
        box_ver_layout.addWidget(self.lbl_engine)

        self.btn_check_update = QPushButton(i18n.t("settings_btn_check_update"))
        self.btn_check_update.setFixedHeight(28)
        self.btn_check_update.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #38BDF8; border: 1px solid #38BDF8; border-radius: 4px; font-weight: 600; padding: 0 10px; }"
            "QPushButton:hover { background-color: #38BDF8; color: #0F172A; }"
        )
        self.btn_check_update.clicked.connect(self._on_check_updates_clicked)
        box_ver_layout.addWidget(self.btn_check_update)

        layout_gen.addWidget(self.group_ver)
        layout_gen.addStretch()

        self.tabs.addTab(tab_general, i18n.t("settings_tab_general"))

        # ── Tab 2: Camera & Performance ───────────────────────────────────────
        tab_camera = QWidget()
        layout_cam = QVBoxLayout(tab_camera)
        layout_cam.setContentsMargins(16, 16, 16, 16)
        layout_cam.setSpacing(16)

        # FPS Control Box
        self.group_fps = QGroupBox(i18n.t("settings_fps_label"))
        self.group_fps.setStyleSheet("QGroupBox { font-weight: bold; color: #E2E8F0; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
        box_fps_layout = QVBoxLayout(self.group_fps)

        self.lbl_fps_desc = QLabel(i18n.t("settings_fps_desc"))
        self.lbl_fps_desc.setWordWrap(True)
        self.lbl_fps_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        box_fps_layout.addWidget(self.lbl_fps_desc)

        fps_row = QHBoxLayout()
        self.fps_combo = QComboBox()
        self.fps_combo.setFixedHeight(32)
        self.fps_combo.addItem("15 FPS (Baixo Consumo / Low CPU)", 15)
        self.fps_combo.addItem("20 FPS (Econômico / Balanced)", 20)
        self.fps_combo.addItem("30 FPS (Padrão Recomendado / Smooth)", 30)
        self.fps_combo.addItem("60 FPS (Alta Fluidez / High Performance)", 60)
        self.fps_combo.currentIndexChanged.connect(self._on_fps_changed)
        fps_row.addWidget(self.fps_combo)
        box_fps_layout.addLayout(fps_row)

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

    def _load_current_values(self):
        # 1. Language
        cur_lang = i18n.get_language()
        for idx in range(self.lang_combo.count()):
            if self.lang_combo.itemData(idx) == cur_lang:
                self.lang_combo.setCurrentIndex(idx)
                break

        # 2. FPS
        try:
            cur_fps = int(database.get_setting("target_fps", "30"))
        except (ValueError, TypeError):
            cur_fps = 30

        for idx in range(self.fps_combo.count()):
            if self.fps_combo.itemData(idx) == cur_fps:
                self.fps_combo.setCurrentIndex(idx)
                break

    def _on_lang_changed(self, index: int):
        code = self.lang_combo.itemData(index)
        if code and code != i18n.get_language():
            i18n.set_language(code)
            database.set_setting("language", code)
            self._retranslate_self()
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

        self.group_lang.setTitle(i18n.t("settings_lang_label"))
        self.lbl_lang_desc.setText(i18n.t("settings_lang_desc"))

        self.group_ver.setTitle(i18n.t("settings_version_label"))
        self.lbl_version.setText(i18n.t("settings_version_info", version=updater.APP_VERSION))
        self.lbl_engine.setText(i18n.t("settings_engine_info"))
        self.btn_check_update.setText(i18n.t("settings_btn_check_update"))

        self.group_fps.setTitle(i18n.t("settings_fps_label"))
        self.lbl_fps_desc.setText(i18n.t("settings_fps_desc"))

        self.btn_done.setText(i18n.t("settings_btn_save"))
