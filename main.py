"""
main.py — Sentinel
==================
Application entry point and main window.

Key Features:
  - Multilingual Support: Portuguese (pt-BR default), English, Spanish with dynamic switching.
  - Scalable User Management: Instant search filter, handles 10,000+ faces smoothly.
  - Safe Face Enrollment: Crash-proof capture flow with thread synchronization.
  - Real-Time Live Feed HUD & Event Logging with CSV Export.
"""

import logging
import os
import sys
from datetime import datetime

import cv2
import numpy as np
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database
import i18n
import updater
from app_paths import get_resource
from camera_worker import CameraWorker
from settings_dialog import SettingsDialog
from user_manager_dialog import UserManagerDialog, UserEditDialog

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
DARK_STYLE_PATH  = get_resource("styles.qss")
LIGHT_STYLE_PATH = get_resource("styles_light.qss")
MAX_LOG_ROWS     = 200   # Cap in-memory log table rows for speed
THUMBNAIL_SIZE = 48    # px — thumbnail column width/height

# Direction color tags
DIRECTION_COLOR = {"ENTER": "#22c55e", "EXIT": "#f97316"}


class SentinelWindow(QMainWindow):
    """
    Main application window with dynamic multilingual translation and scalable UI.
    """

    def __init__(self) -> None:
        super().__init__()

        # ── Initialize DB & Load Saved Language ────────────────────────────
        database.init_db()
        saved_lang = database.get_setting("language", i18n.DEFAULT_LANGUAGE)
        i18n.set_language(saved_lang)

        self.setWindowTitle(i18n.t("app_title"))
        self.resize(1280, 800)
        self.setMinimumSize(960, 620)

        # ── Pending registration state ─────────────────────────────────────
        self._pending_embedding = None   # np.ndarray | None
        self._pending_preview   = None   # QImage | None

        # ── Updater state ──────────────────────────────────────────────────
        self._latest_update_info = None
        self._update_checker = None

        # ── Build UI ───────────────────────────────────────────────────────
        self._build_ui()
        self._apply_stylesheet()

        # ── Camera worker (not started yet) ───────────────────────────────
        self._worker: CameraWorker | None = None

        # ── Populate initial data ─────────────────────────────────────────
        self._refresh_user_table()
        self._restore_logs()

        # ── Background update check (delayed so startup stays instant) ────
        QTimer.singleShot(4000, self._check_updates_background)

    # =========================================================================
    # UI construction
    # =========================================================================

    def _build_ui(self) -> None:
        # ── Menu Bar ───────────────────────────────────────────────────────
        self._build_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 4)
        root_layout.setSpacing(6)

        # ── Top Update Banner (hidden by default) ──────────────────────────
        self._update_banner = self._build_update_banner()
        root_layout.addWidget(self._update_banner)

        # ── Top toolbar ────────────────────────────────────────────────────
        root_layout.addLayout(self._build_toolbar())

        # ── Main split: feed (left) | panels (right) ──────────────────────
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)

        # Left: live feed
        feed_widget = self._build_feed_panel()
        main_splitter.addWidget(feed_widget)

        # Right: event log + user list (vertical splitter)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setHandleWidth(2)
        right_splitter.addWidget(self._build_log_panel())
        right_splitter.addWidget(self._build_user_panel())
        right_splitter.setSizes([400, 260])
        main_splitter.addWidget(right_splitter)

        main_splitter.setSizes([720, 540])
        root_layout.addWidget(main_splitter, stretch=1)

        # ── Bottom: registration bar ───────────────────────────────────────
        root_layout.addWidget(self._build_registration_bar())

        # ── Status bar ─────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(i18n.t("ready_start"))

    # ── Menu Bar ─────────────────────────────────────────────────────────────
    def _build_menu_bar(self) -> None:
        mb = self.menuBar()

        # File Menu
        self.menu_file = mb.addMenu(i18n.t("menu_file"))
        self.action_export_csv = QAction(i18n.t("menu_export_csv"), self)
        self.action_export_csv.triggered.connect(self._export_csv)
        self.menu_file.addAction(self.action_export_csv)

        self.menu_file.addSeparator()

        self.action_exit = QAction(i18n.t("menu_exit"), self)
        self.action_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.action_exit)

        # Users Menu
        self.menu_users = mb.addMenu(i18n.t("menu_users"))
        self.action_manage_users = QAction(i18n.t("menu_manage_users"), self)
        self.action_manage_users.setShortcut("Ctrl+U")
        self.action_manage_users.triggered.connect(self._show_user_manager)
        self.menu_users.addAction(self.action_manage_users)

        self.action_new_user = QAction(i18n.t("menu_new_user"), self)
        self.action_new_user.setShortcut("Ctrl+N")
        self.action_new_user.triggered.connect(self._show_new_user_dialog)
        self.menu_users.addAction(self.action_new_user)

        self.menu_users.addSeparator()

        self.action_export_users = QAction(i18n.t("menu_export_users"), self)
        self.action_export_users.triggered.connect(self._export_users_csv)
        self.menu_users.addAction(self.action_export_users)

        # Settings Menu (beside File, Users, and Help)
        self.menu_settings = mb.addMenu(i18n.t("menu_settings"))
        self.action_open_settings = QAction(i18n.t("menu_open_settings"), self)
        self.action_open_settings.setShortcut("Ctrl+,")
        self.action_open_settings.triggered.connect(lambda: self._show_settings(tab_idx=0))
        self.menu_settings.addAction(self.action_open_settings)

        self.menu_settings.addSeparator()

        self.action_fps_settings = QAction(i18n.t("menu_fps_settings"), self)
        self.action_fps_settings.triggered.connect(lambda: self._show_settings(tab_idx=1))
        self.menu_settings.addAction(self.action_fps_settings)

        self.action_lang_settings = QAction(i18n.t("menu_lang_settings"), self)
        self.action_lang_settings.triggered.connect(lambda: self._show_settings(tab_idx=0))
        self.menu_settings.addAction(self.action_lang_settings)

        # Help Menu
        self.menu_help = mb.addMenu(i18n.t("menu_help"))
        self.action_check_updates = QAction(i18n.t("menu_check_updates"), self)
        self.action_check_updates.triggered.connect(self._check_updates_manual)
        self.menu_help.addAction(self.action_check_updates)

        self.menu_help.addSeparator()

        self.action_about = QAction(i18n.t("menu_about"), self)
        self.action_about.triggered.connect(self._show_about)
        self.menu_help.addAction(self.action_about)

    # ── Update Banner ────────────────────────────────────────────────────────
    def _build_update_banner(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("update_banner")
        frame.setStyleSheet(
            "QFrame#update_banner { background-color: #0D2818; border: 1px solid #10B981; border-radius: 6px; padding: 4px 8px; }"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        self.update_banner_label = QLabel(i18n.t("update_banner_text", version=""))
        self.update_banner_label.setStyleSheet("color: #34D399; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.update_banner_label)

        layout.addStretch()

        self.btn_banner_update = QPushButton(i18n.t("update_btn_update"))
        self.btn_banner_update.setFixedHeight(26)
        self.btn_banner_update.setStyleSheet(
            "QPushButton { background-color: #10B981; color: #042F1A; font-weight: bold; border-radius: 4px; padding: 0 12px; }"
            "QPushButton:hover { background-color: #34D399; }"
        )
        self.btn_banner_update.clicked.connect(self._on_update_banner_click)
        layout.addWidget(self.btn_banner_update)

        self.btn_banner_dismiss = QPushButton("X")
        self.btn_banner_dismiss.setFixedSize(22, 22)
        self.btn_banner_dismiss.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6EE7B7; border: none; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(255,255,255,0.1); border-radius: 3px; }"
        )
        self.btn_banner_dismiss.clicked.connect(lambda: frame.setVisible(False))
        layout.addWidget(self.btn_banner_dismiss)

        frame.setVisible(False)
        return frame

    # ── Toolbar ───────────────────────────────────────────────────────────────
    def _build_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Start / Stop buttons
        self.btn_start = QPushButton(i18n.t("start"))
        self.btn_start.setObjectName("btn_success")
        self.btn_start.setFixedHeight(32)
        self.btn_start.clicked.connect(self._start_camera)

        self.btn_stop = QPushButton(i18n.t("stop"))
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setFixedHeight(32)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_camera)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Tripwire slider
        self.tw_label = QLabel(i18n.t("tripwire_label"))
        self.tw_label.setObjectName("subtext")
        self.tw_slider = QSlider(Qt.Orientation.Horizontal)
        self.tw_slider.setRange(5, 95)
        self.tw_slider.setValue(50)
        self.tw_slider.setFixedWidth(140)
        self.tw_slider.setFixedHeight(24)
        self.tw_slider.setToolTip(i18n.t("tripwire_tooltip"))
        self.tw_value_label = QLabel("50%")
        self.tw_value_label.setObjectName("subtext")
        self.tw_value_label.setFixedWidth(34)
        self.tw_slider.valueChanged.connect(self._on_tripwire_changed)

        # Language Selector
        self.lang_label = QLabel(i18n.t("language_label"))
        self.lang_label.setObjectName("subtext")
        self.lang_selector = QComboBox()
        self.lang_selector.setFixedHeight(32)
        self.lang_selector.setFixedWidth(145)

        # Populate language options
        for code, name in i18n.LANGUAGES.items():
            self.lang_selector.addItem(name, code)

        current_lang = i18n.get_language()
        for idx in range(self.lang_selector.count()):
            if self.lang_selector.itemData(idx) == current_lang:
                self.lang_selector.setCurrentIndex(idx)
                break
        self.lang_selector.currentIndexChanged.connect(self._on_language_changed)

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(spacer)
        layout.addWidget(self.tw_label)
        layout.addWidget(self.tw_slider)
        layout.addWidget(self.tw_value_label)
        layout.addWidget(self.lang_label)
        layout.addWidget(self.lang_selector)
        return layout

    # ── Live feed panel ───────────────────────────────────────────────────────
    def _build_feed_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel_card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.feed_title = QLabel(i18n.t("live_feed"))
        self.feed_title.setObjectName("section_title")
        layout.addWidget(self.feed_title)

        self.video_label = QLabel(i18n.t("camera_offline"))
        self.video_label.setObjectName("video_label")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.video_label.setMinimumSize(400, 300)
        layout.addWidget(self.video_label, stretch=1)

        return frame

    # ── Event log panel ───────────────────────────────────────────────────────
    def _build_log_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel_card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header row
        header_row = QHBoxLayout()
        self.log_title = QLabel(i18n.t("event_log"))
        self.log_title.setObjectName("section_title")
        header_row.addWidget(self.log_title)
        header_row.addStretch()

        self.btn_clear = QPushButton(i18n.t("btn_clear"))
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.setToolTip(i18n.t("clear_tooltip"))
        self.btn_clear.clicked.connect(self._clear_log_display)

        self.btn_export = QPushButton(i18n.t("btn_export"))
        self.btn_export.setFixedHeight(26)
        self.btn_export.clicked.connect(self._export_csv)

        header_row.addWidget(self.btn_clear)
        header_row.addWidget(self.btn_export)
        layout.addLayout(header_row)

        # Table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(
            [
                i18n.t("col_time"),
                i18n.t("col_thumb"),
                i18n.t("col_name"),
                i18n.t("col_direction"),
                i18n.t("col_emotion"),
            ]
        )
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setShowGrid(False)
        self.log_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.log_table.setColumnWidth(0, 70)
        self.log_table.setColumnWidth(1, THUMBNAIL_SIZE + 8)
        self.log_table.setColumnWidth(3, 85)
        self.log_table.setColumnWidth(4, 95)
        layout.addWidget(self.log_table, stretch=1)

        return frame

    # ── User panel (Scalable with Search Bar) ─────────────────────────────────
    def _build_user_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel_card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header row with title & user count badge
        header_row = QHBoxLayout()
        self.user_title = QLabel(i18n.t("registered_users"))
        self.user_title.setObjectName("section_title")

        self.user_count_label = QLabel(i18n.t("user_count", count=0))
        self.user_count_label.setObjectName("subtext")

        header_row.addWidget(self.user_title)
        header_row.addStretch()
        header_row.addWidget(self.user_count_label)

        self.btn_open_user_mgr = QPushButton(i18n.t("btn_manage_users"))
        self.btn_open_user_mgr.setFixedHeight(24)
        self.btn_open_user_mgr.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_open_user_mgr.clicked.connect(self._show_user_manager)
        header_row.addWidget(self.btn_open_user_mgr)
        layout.addLayout(header_row)

        # Search / filter box
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText(i18n.t("search_placeholder"))
        self.user_search_input.setFixedHeight(26)
        self.user_search_input.textChanged.connect(self._refresh_user_table)
        layout.addWidget(self.user_search_input)

        # Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(
            [
                i18n.t("col_name"),
                i18n.t("col_role"),
                i18n.t("col_registered_at"),
                "",
            ]
        )
        self.user_table.setAlternatingRowColors(True)
        self.user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setShowGrid(False)
        self.user_table.cellDoubleClicked.connect(self._on_user_table_double_clicked)
        self.user_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.user_table.setColumnWidth(1, 90)
        self.user_table.setColumnWidth(2, 130)
        self.user_table.setColumnWidth(3, 40)
        layout.addWidget(self.user_table, stretch=1)

        return frame

    # ── Registration bar ──────────────────────────────────────────────────────
    def _build_registration_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel_card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.reg_title = QLabel(i18n.t("register_section"))
        self.reg_title.setObjectName("section_title")
        layout.addWidget(self.reg_title)

        self.reg_name_label = QLabel(i18n.t("name_label"))
        self.reg_name_label.setObjectName("subtext")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(i18n.t("name_placeholder"))
        self.name_input.setFixedWidth(160)
        self.name_input.setFixedHeight(30)

        self.reg_role_label = QLabel(i18n.t("role_label"))
        self.reg_role_label.setObjectName("subtext")
        self.role_selector = QComboBox()
        self.role_selector.addItems(i18n.get_roles_list())
        self.role_selector.setFixedHeight(30)
        self.role_selector.setFixedWidth(115)

        self.btn_capture = QPushButton(i18n.t("btn_capture"))
        self.btn_capture.setObjectName("btn_primary")
        self.btn_capture.setFixedHeight(30)
        self.btn_capture.setToolTip(i18n.t("btn_capture_tooltip"))
        self.btn_capture.clicked.connect(self._request_capture)

        self.btn_save = QPushButton(i18n.t("btn_save"))
        self.btn_save.setObjectName("btn_success")
        self.btn_save.setFixedHeight(30)
        self.btn_save.setEnabled(False)
        self.btn_save.setToolTip(i18n.t("btn_save_tooltip"))
        self.btn_save.clicked.connect(self._save_registration)

        self.btn_full_register = QPushButton(i18n.t("btn_full_register"))
        self.btn_full_register.setFixedHeight(30)
        self.btn_full_register.setToolTip(i18n.t("user_dialog_create_title"))
        self.btn_full_register.clicked.connect(self._show_new_user_dialog)

        self.capture_status = QLabel(i18n.t("status_no_face_yet"))
        self.capture_status.setObjectName("subtext")

        layout.addWidget(self.reg_name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.reg_role_label)
        layout.addWidget(self.role_selector)
        layout.addWidget(self.btn_capture)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_full_register)
        layout.addWidget(self.capture_status)
        layout.addStretch()

        return frame

    # =========================================================================
    # Multilingual Re-translation
    # =========================================================================

    def _on_language_changed(self, index: int) -> None:
        """Handle language selection change in toolbar."""
        code = self.lang_selector.itemData(index)
        if code:
            i18n.set_language(code)
            database.set_setting("language", code)
            self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        """Dynamically update all visible text in the UI to match the active language."""
        self.setWindowTitle(i18n.t("app_title"))

        # Menu bar
        if hasattr(self, "menu_file"):
            self.menu_file.setTitle(i18n.t("menu_file"))
            self.action_export_csv.setText(i18n.t("menu_export_csv"))
            self.action_exit.setText(i18n.t("menu_exit"))
        if hasattr(self, "menu_users"):
            self.menu_users.setTitle(i18n.t("menu_users"))
            self.action_manage_users.setText(i18n.t("menu_manage_users"))
            self.action_new_user.setText(i18n.t("menu_new_user"))
            self.action_export_users.setText(i18n.t("menu_export_users"))
        if hasattr(self, "menu_settings"):
            self.menu_settings.setTitle(i18n.t("menu_settings"))
            self.action_open_settings.setText(i18n.t("menu_open_settings"))
            self.action_fps_settings.setText(i18n.t("menu_fps_settings"))
            self.action_lang_settings.setText(i18n.t("menu_lang_settings"))
        if hasattr(self, "menu_help"):
            self.menu_help.setTitle(i18n.t("menu_help"))
            self.action_check_updates.setText(i18n.t("menu_check_updates"))
            self.action_about.setText(i18n.t("menu_about"))

        if hasattr(self, "btn_open_user_mgr"):
            self.btn_open_user_mgr.setText(i18n.t("btn_manage_users"))
        if hasattr(self, "btn_full_register"):
            self.btn_full_register.setText(i18n.t("btn_full_register"))
            self.btn_full_register.setToolTip(i18n.t("user_dialog_create_title"))

        # Update banner
        if hasattr(self, "update_banner_label") and self._latest_update_info:
            self.update_banner_label.setText(i18n.t("update_banner_text", version=self._latest_update_info.version))
        if hasattr(self, "btn_banner_update"):
            self.btn_banner_update.setText(i18n.t("update_btn_update"))

        self.btn_start.setText(i18n.t("start"))
        self.btn_stop.setText(i18n.t("stop"))
        self.tw_label.setText(i18n.t("tripwire_label"))
        self.tw_slider.setToolTip(i18n.t("tripwire_tooltip"))
        self.lang_label.setText(i18n.t("language_label"))

        self.feed_title.setText(i18n.t("live_feed"))
        if not self._worker or not self._worker.isRunning():
            self.video_label.setText(i18n.t("camera_offline"))

        self.log_title.setText(i18n.t("event_log"))
        self.btn_clear.setText(i18n.t("btn_clear"))
        self.btn_clear.setToolTip(i18n.t("clear_tooltip"))
        self.btn_export.setText(i18n.t("btn_export"))
        self.log_table.setHorizontalHeaderLabels(
            [
                i18n.t("col_time"),
                i18n.t("col_thumb"),
                i18n.t("col_name"),
                i18n.t("col_direction"),
                i18n.t("col_emotion"),
            ]
        )

        self.user_title.setText(i18n.t("registered_users"))
        self.user_search_input.setPlaceholderText(i18n.t("search_placeholder"))
        self.user_table.setHorizontalHeaderLabels(
            [
                i18n.t("col_name"),
                i18n.t("col_role"),
                i18n.t("col_registered_at"),
                "",
            ]
        )

        self.reg_title.setText(i18n.t("register_section"))
        self.reg_name_label.setText(i18n.t("name_label"))
        self.name_input.setPlaceholderText(i18n.t("name_placeholder"))
        self.reg_role_label.setText(i18n.t("role_label"))

        cur_role_idx = self.role_selector.currentIndex()
        self.role_selector.clear()
        self.role_selector.addItems(i18n.get_roles_list())
        self.role_selector.setCurrentIndex(max(0, cur_role_idx))

        self.btn_capture.setText(i18n.t("btn_capture"))
        self.btn_capture.setToolTip(i18n.t("btn_capture_tooltip"))
        self.btn_save.setText(i18n.t("btn_save"))
        self.btn_save.setToolTip(i18n.t("btn_save_tooltip"))

        if self._pending_embedding is not None:
            self.capture_status.setText(i18n.t("status_captured_success"))
        else:
            self.capture_status.setText(i18n.t("status_no_face_yet"))

        self.status_bar.showMessage(i18n.t("ready_start"))
        self._refresh_user_table()

    # =========================================================================
    # Stylesheet
    # =========================================================================

    def _apply_stylesheet(self) -> None:
        theme = database.get_setting("theme", "dark")
        target_path = LIGHT_STYLE_PATH if theme == "light" else DARK_STYLE_PATH
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as exc:
                logger.warning("Could not read stylesheet: %s", exc)

    # =========================================================================
    # Camera lifecycle
    # =========================================================================

    def _start_camera(self) -> None:
        """Create and start the CameraWorker thread."""
        if self._worker and self._worker.isRunning():
            return

        try:
            cam_idx = int(database.get_setting("camera_index", "0"))
        except (ValueError, TypeError):
            cam_idx = 0

        self._worker = CameraWorker(camera_index=cam_idx)

        # Connect signals
        self._worker.frame_ready.connect(self._update_frame)
        self._worker.event_occurred.connect(self._on_event)
        self._worker.status_message.connect(self.status_bar.showMessage)
        self._worker.capture_done.connect(self._on_capture_done)

        # Apply tripwire ratio
        self._worker.set_tripwire_ratio(self.tw_slider.value() / 100.0)

        self._worker.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _stop_camera(self) -> None:
        """Stop the CameraWorker thread gracefully."""
        if self._worker:
            self._worker.stop()
            self._worker.wait(3000)
            self._worker = None

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.video_label.setText(i18n.t("camera_offline"))
        self.video_label.setPixmap(QPixmap())
        self.status_bar.showMessage(i18n.t("camera_stopped"))

    # =========================================================================
    # Slots — Live feed & events
    # =========================================================================

    @Slot(QImage)
    def _update_frame(self, q_img: QImage) -> None:
        """Render a new annotated frame from worker to video label."""
        pix = QPixmap.fromImage(q_img)
        scaled = pix.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.video_label.setPixmap(scaled)

    @Slot(dict)
    def _on_event(self, event: dict) -> None:
        """Handle an ENTER/EXIT event emitted by the worker."""
        direction = event.get("direction", "?")
        name      = event.get("name", "Unknown")
        emotion   = event.get("emotion", "Neutral")
        timestamp = event.get("timestamp", "")
        crop_path = event.get("crop_path")

        # Cap row count
        if self.log_table.rowCount() >= MAX_LOG_ROWS:
            self.log_table.removeRow(self.log_table.rowCount() - 1)

        self.log_table.insertRow(0)

        # Time
        t_item = QTableWidgetItem(timestamp)
        t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_table.setItem(0, 0, t_item)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if crop_path and os.path.isfile(crop_path):
            pix = QPixmap(crop_path).scaled(
                THUMBNAIL_SIZE, THUMBNAIL_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            thumb_label.setPixmap(pix)
        else:
            thumb_label.setText(i18n.t("no_image"))
        self.log_table.setCellWidget(0, 1, thumb_label)
        self.log_table.setRowHeight(0, THUMBNAIL_SIZE + 4)

        # Name
        n_item = QTableWidgetItem(name)
        self.log_table.setItem(0, 2, n_item)

        # Direction — Localized label
        loc_dir = i18n.translate_direction(direction)
        dir_label = QLabel(loc_dir)
        dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = DIRECTION_COLOR.get(direction, "#e6edf3")
        dir_label.setStyleSheet(
            f"color: {color}; font-weight: 600; font-size: 13px;"
        )
        self.log_table.setCellWidget(0, 3, dir_label)

        # Emotion — Localized label
        loc_emotion = i18n.translate_emotion(emotion)
        e_item = QTableWidgetItem(loc_emotion)
        e_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_table.setItem(0, 4, e_item)

        # Flash status bar
        self.status_bar.showMessage(f"{loc_dir}: {name} [{loc_emotion}]")

    # =========================================================================
    # Tripwire slider
    # =========================================================================

    @Slot(int)
    def _on_tripwire_changed(self, value: int) -> None:
        self.tw_value_label.setText(f"{value}%")
        if self._worker:
            self._worker.set_tripwire_ratio(value / 100.0)

    # =========================================================================
    # Crash-Proof Registration Flow
    # =========================================================================

    def _request_capture(self) -> None:
        """Trigger face capture with state and input validation."""
        if not self._worker or not self._worker.isRunning():
            QMessageBox.warning(
                self,
                i18n.t("alert_cam_not_running_title"),
                i18n.t("alert_cam_not_running_msg"),
            )
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                i18n.t("alert_name_required_title"),
                i18n.t("alert_name_required_msg"),
            )
            return

        self.capture_status.setText(i18n.t("status_capturing"))
        self.btn_capture.setEnabled(False)
        self._worker.request_capture()

    @Slot(object, object)
    def _on_capture_done(self, embedding, q_img: QImage) -> None:
        """Safely handle capture result from worker."""
        try:
            self.btn_capture.setEnabled(True)

            pix = QPixmap.fromImage(q_img)
            scaled = pix.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self.video_label.setPixmap(scaled)

            if embedding is not None:
                self._pending_embedding = embedding
                self.btn_save.setEnabled(True)
                self.capture_status.setText(i18n.t("status_captured_success"))
            else:
                self._pending_embedding = None
                self.btn_save.setEnabled(False)
                self.capture_status.setText(i18n.t("status_no_face_detected"))
        except Exception as exc:
            logger.exception("Error in _on_capture_done: %s", exc)

    def _save_registration(self) -> None:
        """Persist new person in database with thread-safe worker notification."""
        try:
            name = self.name_input.text().strip()
            role = self.role_selector.currentText()

            if not name:
                QMessageBox.warning(
                    self,
                    i18n.t("alert_name_required_title"),
                    i18n.t("alert_name_required_msg"),
                )
                return

            if self._pending_embedding is None:
                QMessageBox.warning(
                    self,
                    i18n.t("alert_no_face_title"),
                    i18n.t("alert_no_face_msg"),
                )
                return

            # Store in DB with compact binary float buffer
            database.add_user(name, role, self._pending_embedding)

            self._pending_embedding = None
            self.btn_save.setEnabled(False)
            self.capture_status.setText(i18n.t("status_saved_success"))
            self.name_input.clear()

            # Refresh worker's vectorized 2D matrix
            if self._worker:
                self._worker.reload_embeddings()

            self._refresh_user_table()
        except Exception as exc:
            logger.exception("Failed to save person: %s", exc)
            QMessageBox.critical(
                self,
                i18n.t("error_saving_title"),
                i18n.t("error_saving_msg", error=str(exc)),
            )

    # =========================================================================
    # User table management (Scalable with Filter & Limit)
    # =========================================================================

    def _refresh_user_table(self) -> None:
        """Fast, paginated user table population. Handles 10,000+ users instantly."""
        try:
            search_query = self.user_search_input.text().strip() if hasattr(self, "user_search_input") else ""
            total_count = database.get_user_count(search_query)

            if hasattr(self, "user_count_label"):
                self.user_count_label.setText(i18n.t("user_count", count=total_count))

            # Fetch up to 100 matching users to keep UI instant
            users = database.get_users_filtered(query=search_query, limit=100)

            self.user_table.setRowCount(0)
            for uid, name, role, reg_at in users:
                row = self.user_table.rowCount()
                self.user_table.insertRow(row)

                item_name = QTableWidgetItem(name)
                item_name.setData(Qt.ItemDataRole.UserRole, uid)
                self.user_table.setItem(row, 0, item_name)
                self.user_table.setItem(row, 1, QTableWidgetItem(role))

                reg_display = reg_at[:16] if len(reg_at) >= 16 else reg_at
                self.user_table.setItem(row, 2, QTableWidgetItem(reg_display))

                # Delete button
                del_btn = QPushButton("X")
                del_btn.setObjectName("btn_icon")
                del_btn.setToolTip(i18n.t("btn_delete_tooltip", name=name))
                del_btn.clicked.connect(lambda checked, u=uid, n=name: self._delete_user(u, n))
                self.user_table.setCellWidget(row, 3, del_btn)

        except Exception as exc:
            logger.exception("Failed to refresh user table: %s", exc)

    def _delete_user(self, user_id: int, name: str) -> None:
        """Confirm and delete a registered user."""
        try:
            reply = QMessageBox.question(
                self,
                i18n.t("confirm_unregister_title"),
                i18n.t("confirm_unregister_msg", name=name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                database.delete_user(user_id)
                if self._worker:
                    self._worker.reload_embeddings()
                self._refresh_user_table()
                self.status_bar.showMessage(i18n.t("user_removed_status", name=name))
        except Exception as exc:
            logger.exception("Failed to delete user: %s", exc)
            QMessageBox.critical(
                self,
                i18n.t("error_deleting_title"),
                i18n.t("error_deleting_msg", error=str(exc)),
            )

    def _show_user_manager(self) -> None:
        """Open the dedicated User Management Center dialog."""
        dlg = UserManagerDialog(camera_worker=self._worker, parent=self)
        dlg.database_changed.connect(self._on_user_database_changed)
        dlg.exec()

    def _show_new_user_dialog(self) -> None:
        """Open the detailed New User Registration dialog."""
        dlg = UserEditDialog(parent=self, camera_worker=self._worker)
        dlg.user_saved.connect(lambda uid: self._on_user_database_changed())
        dlg.exec()

    def _on_user_table_double_clicked(self, row: int, col: int) -> None:
        """Open user editor when double clicking row in sidebar table."""
        name_item = self.user_table.item(row, 0)
        if name_item:
            uid = name_item.data(Qt.ItemDataRole.UserRole)
            if uid:
                dlg = UserEditDialog(user_id=uid, parent=self, camera_worker=self._worker)
                dlg.user_saved.connect(lambda u: self._on_user_database_changed())
                dlg.exec()

    def _on_user_database_changed(self) -> None:
        """Sync worker and reload sidebar table whenever user database changes."""
        if self._worker:
            self._worker.reload_embeddings()
        self._refresh_user_table()

    def _export_users_csv(self) -> None:
        """Export all registered users to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.t("export_complete_title"),
            "usuarios_sentinel.csv",
            i18n.t("csv_filter"),
        )
        if not file_path:
            return
        try:
            count = database.export_users_csv(file_path)
            QMessageBox.information(
                self,
                i18n.t("export_complete_title"),
                i18n.t("export_complete_msg", count=count, path=file_path),
            )
        except Exception as exc:
            logger.exception("Failed to export users to CSV: %s", exc)
            QMessageBox.critical(
                self,
                i18n.t("error_saving_title"),
                str(exc),
            )

    # =========================================================================
    # Log panel helpers
    # =========================================================================

    def _restore_logs(self) -> None:
        """Populate the log table with the most recent 100 events from the DB."""
        rows = database.get_recent_logs(limit=100)
        for row in rows:
            self._on_event(
                {
                    "name":      row["user_name"],
                    "direction": row["direction"],
                    "emotion":   row["emotion"],
                    "timestamp": row["timestamp"][11:19] if row["timestamp"] else "",
                    "crop_path": row["crop_path"],
                }
            )

    def _clear_log_display(self) -> None:
        self.log_table.setRowCount(0)

    def _export_csv(self) -> None:
        """Open a save dialog and export all logs to a CSV file."""
        default_name = f"{i18n.t('csv_default_name')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.t("btn_export"),
            default_name,
            i18n.t("csv_filter"),
        )
        if path:
            count = database.export_logs_csv(path)
            QMessageBox.information(
                self,
                i18n.t("export_complete_title"),
                i18n.t("export_complete_msg", count=count, path=path),
            )

    # =========================================================================
    # Auto-Updater & About Dialog
    # =========================================================================

    def _check_updates_background(self) -> None:
        """Run non-intrusive background update check."""
        try:
            self._update_checker = updater.UpdateCheckWorker(parent=self)
            self._update_checker.update_available.connect(self._on_update_available_background)
            self._update_checker.start()
        except Exception as exc:
            logger.debug("Background update check error: %s", exc)

    def _on_update_available_background(self, info: updater.UpdateInfo) -> None:
        """Called when a new release is found during background check."""
        self._latest_update_info = info
        self.update_banner_label.setText(i18n.t("update_banner_text", version=info.version))
        self._update_banner.setVisible(True)
        self.status_bar.showMessage(i18n.t("update_banner_text", version=info.version))

    def _on_update_banner_click(self) -> None:
        if self._latest_update_info:
            dlg = updater.UpdateDialog(self._latest_update_info, parent=self)
            dlg.exec()

    def _check_updates_manual(self) -> None:
        """Manual check initiated from Help menu."""
        self.status_bar.showMessage(i18n.t("update_checking"))
        self._manual_checker = updater.UpdateCheckWorker(parent=self)

        def on_avail(info: updater.UpdateInfo):
            self._latest_update_info = info
            self.status_bar.showMessage(i18n.t("update_banner_text", version=info.version))
            dlg = updater.UpdateDialog(info, parent=self)
            dlg.exec()

        def on_current(ver: str):
            self.status_bar.showMessage(i18n.t("ready_start"))
            QMessageBox.information(
                self,
                i18n.t("update_up_to_date_title"),
                i18n.t("update_up_to_date_msg", version=ver),
            )

        def on_err(err: str):
            self.status_bar.showMessage(i18n.t("ready_start"))
            QMessageBox.warning(
                self,
                i18n.t("update_error_title"),
                i18n.t("update_error_msg", error=err),
            )

        self._manual_checker.update_available.connect(on_avail)
        self._manual_checker.up_to_date.connect(on_current)
        self._manual_checker.check_error.connect(on_err)
        self._manual_checker.start()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            i18n.t("about_title"),
            i18n.t("about_body", version=updater.APP_VERSION),
        )

    def _show_settings(self, tab_idx: int = 0) -> None:
        """Open the Settings dialog modal."""
        dlg = SettingsDialog(self, on_check_updates_cb=self._check_updates_manual, initial_tab=tab_idx)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self) -> None:
        """Callback when theme, language, camera, or FPS is modified in settings."""
        # 1. Apply active theme (Dark / Light)
        self._apply_stylesheet()

        # 2. Sync toolbar language selector
        cur_lang = i18n.get_language()
        for idx in range(self.lang_selector.count()):
            if self.lang_selector.itemData(idx) == cur_lang:
                self.lang_selector.blockSignals(True)
                self.lang_selector.setCurrentIndex(idx)
                self.lang_selector.blockSignals(False)
                break

        # 3. Retranslate all UI labels
        self._retranslate_ui()

        # 4. Apply FPS if camera is currently running
        if self._worker:
            try:
                fps = int(database.get_setting("target_fps", "30"))
                self._worker.set_target_fps(fps)
            except Exception as exc:
                logger.debug("Failed to set target FPS: %s", exc)

        # 5. Check if camera device changed while running
        try:
            target_cam = int(database.get_setting("camera_index", "0"))
            if self._worker and self._worker.isRunning():
                if self._worker.camera_index != target_cam:
                    logger.info("Switching running camera from %d to %d", self._worker.camera_index, target_cam)
                    self._stop_camera()
                    self._start_camera()
        except Exception as exc:
            logger.debug("Error updating camera device: %s", exc)

    # =========================================================================
    # Window close
    # =========================================================================

    def closeEvent(self, event) -> None:
        """Stop the camera worker before closing."""
        self._stop_camera()
        event.accept()


# ==============================================================================
def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Sentinel")
    app.setOrganizationName("Sentinel")

    window = SentinelWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
