"""
history_dialog.py - Facial Recordings & Event History Center for Sentinel v1.0.8

Provides a comprehensive, searchable, filterable history dialog for all
facial recordings (ENTER/EXIT events) stored in the SQLite database.
Includes thumbnail previews, direction badges, stats cards, and CSV export.
"""

import os
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QFrame,
    QWidget,
)

import i18n
import database

logger = logging.getLogger("Sentinel.HistoryDialog")


# ── Thumbnail / Avatar Helper ────────────────────────────────────────────────

def create_rounded_thumb(pixmap: QPixmap, size: int = 44) -> QPixmap:
    """Create a rounded rectangular thumbnail pixmap for table cells."""
    scaled = pixmap.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, 6, 6)
    painter.setClipPath(path)

    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()

    return result


def create_placeholder_thumb(size: int = 44, text: str = "👤") -> QPixmap:
    """Generate a placeholder thumbnail when no crop image exists."""
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, 6, 6)
    painter.setClipPath(path)

    painter.fillRect(0, 0, size, size, QColor("#1E293B"))
    painter.setPen(QColor("#94A3B8"))
    font = painter.font()
    font.setPixelSize(size // 2)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, text)
    painter.end()

    return result


# ── Large Image Preview Dialog ────────────────────────────────────────────────

class ImagePreviewDialog(QDialog):
    """Full-size preview popup for a recorded facial crop image."""

    def __init__(self, crop_path: str, title: str = "", details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title or i18n.t("history_dialog_title"))
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(360, 420)
        self.resize(480, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Image view
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(
            "background-color: #0A0F1D; border-radius: 8px; border: 1px solid #1E293B;"
        )

        if os.path.exists(crop_path):
            pix = QPixmap(crop_path)
            if not pix.isNull():
                self.img_label.setPixmap(
                    pix.scaled(
                        400,
                        400,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                self.img_label.setText("Erro ao carregar imagem")
        else:
            self.img_label.setText("Arquivo de imagem não encontrado")

        layout.addWidget(self.img_label, stretch=1)

        # Details
        if details:
            lbl_info = QLabel(details)
            lbl_info.setStyleSheet("color: #94A3B8; font-size: 13px;")
            lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_info)

        # Close button
        btn_close = QPushButton(i18n.t("update_cancel") or "Fechar")
        btn_close.setFixedHeight(34)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# ── Full Facial Event History Dialog ──────────────────────────────────────────

class EventHistoryDialog(QDialog):
    """
    Dedicated Facial Recordings & Event History Center.
    Displays all historical entry/exit events from SQLite with:
      - Real-time search by name or emotion
      - Direction filtering (ENTER / EXIT / All)
      - Row limit selector (100 / 250 / 500 / All)
      - Summary statistics cards (Total, Entradas, Saídas, Pessoas Únicas)
      - Face thumbnails with high-res preview on double-click
      - CSV export
      - Single-record deletion
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("history_dialog_title"))
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(850, 520)
        self.resize(1020, 640)

        self._current_logs: List[Dict[str, Any]] = []

        self._init_ui()
        self._refresh_stats()
        self._load_logs()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        # ── Header & Stats Bar ───────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel(i18n.t("history_dialog_title"))
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        subtitle_lbl = QLabel(i18n.t("history_dialog_subtitle"))
        subtitle_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Stats Cards
        self.stat_total_val = QLabel("0")
        self.stat_enters_val = QLabel("0")
        self.stat_exits_val = QLabel("0")
        self.stat_unique_val = QLabel("0")

        header_row.addWidget(self._create_stat_card(i18n.t("stat_total_events"), self.stat_total_val, "#38BDF8"))
        header_row.addWidget(self._create_stat_card(i18n.t("stat_enters"), self.stat_enters_val, "#00FF88"))
        header_row.addWidget(self._create_stat_card(i18n.t("stat_exits"), self.stat_exits_val, "#FF8800"))
        header_row.addWidget(self._create_stat_card(i18n.t("stat_unique_persons"), self.stat_unique_val, "#A78BFA"))

        # Export CSV Button
        self.btn_export = QPushButton(f"📥 {i18n.t('btn_export_users')}")
        self.btn_export.setFixedHeight(36)
        self.btn_export.setStyleSheet(
            "QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 0 14px; font-weight: bold; } "
            "QPushButton:hover { background-color: #334155; }"
        )
        self.btn_export.clicked.connect(self._export_csv)
        header_row.addWidget(self.btn_export)

        root_layout.addLayout(header_row)

        # ── Filter & Search Bar ──────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        # Search Bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(f"🔍 {i18n.t('history_search_placeholder')}")
        self.search_edit.setFixedHeight(34)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._load_logs)
        filter_row.addWidget(self.search_edit, stretch=2)

        # Direction Filter Combo
        self.combo_direction = QComboBox()
        self.combo_direction.setFixedHeight(34)
        self.combo_direction.addItem(i18n.t("filter_all_directions"), "all")
        self.combo_direction.addItem(f"🟢 {i18n.t('filter_enter')}", "ENTER")
        self.combo_direction.addItem(f"🔴 {i18n.t('filter_exit')}", "EXIT")
        self.combo_direction.currentIndexChanged.connect(self._load_logs)
        filter_row.addWidget(self.combo_direction)

        # Limit Filter Combo
        self.combo_limit = QComboBox()
        self.combo_limit.setFixedHeight(34)
        self.combo_limit.addItem(i18n.t("filter_limit_100"), 100)
        self.combo_limit.addItem(i18n.t("filter_limit_250"), 250)
        self.combo_limit.addItem(i18n.t("filter_limit_500"), 500)
        self.combo_limit.addItem(i18n.t("filter_limit_all"), 0)
        self.combo_limit.currentIndexChanged.connect(self._load_logs)
        filter_row.addWidget(self.combo_limit)

        # Refresh Button
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedSize(34, 34)
        self.btn_refresh.setToolTip("Atualizar")
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; font-size: 16px; font-weight: bold; } "
            "QPushButton:hover { background-color: #334155; }"
        )
        self.btn_refresh.clicked.connect(self._refresh_all)
        filter_row.addWidget(self.btn_refresh)

        root_layout.addLayout(filter_row)

        # ── Event Logs Table ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            i18n.t("col_log_thumb"),
            i18n.t("col_log_time"),
            i18n.t("col_log_name"),
            i18n.t("col_log_direction"),
            i18n.t("col_log_emotion"),
            i18n.t("col_log_actions"),
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setIconSize(QSize(44, 44))

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 90)

        # Double click to view full image
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)

        root_layout.addWidget(self.table, stretch=1)

    def _create_stat_card(self, label: str, value_label: QLabel, color_hex: str) -> QFrame:
        """Create a compact badge card for summary statistics."""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 4px 10px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color_hex};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(label)
        title.setStyleSheet("font-size: 10px; color: #64748B; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(title)
        return card

    # ── Data Loading & Table Population ──────────────────────────────────────

    def _refresh_stats(self):
        """Fetch and update aggregate statistics counters."""
        try:
            stats = database.get_logs_stats()
            self.stat_total_val.setText(f"{stats.get('total', 0):,}")
            self.stat_enters_val.setText(f"{stats.get('enters', 0):,}")
            self.stat_exits_val.setText(f"{stats.get('exits', 0):,}")
            self.stat_unique_val.setText(f"{stats.get('unique_persons', 0):,}")
        except Exception as exc:
            logger.error("Error refreshing stats: %s", exc)

    def _refresh_all(self):
        """Reload both stats counters and the table records."""
        self._refresh_stats()
        self._load_logs()

    def _load_logs(self):
        """Load filtered logs and render into table."""
        query = self.search_edit.text().strip()
        direction = self.combo_direction.currentData()
        limit_val = self.combo_limit.currentData()
        limit = limit_val if limit_val and limit_val > 0 else 10000

        try:
            logs = database.get_logs_filtered(
                query=query,
                direction=direction,
                limit=limit,
                offset=0,
            )
            self._current_logs = logs
            self._populate_table(logs)
        except Exception as exc:
            logger.error("Failed to load event history: %s", exc)

    def _populate_table(self, logs: List[Dict[str, Any]]):
        """Render rows into QTableWidget."""
        self.table.setRowCount(0)
        self.table.setRowCount(len(logs))

        for row_idx, log in enumerate(logs):
            self.table.setRowHeight(row_idx, 52)

            # 1. Photo thumbnail
            crop_path = log.get("crop_path") or ""
            thumb_item = QTableWidgetItem()
            thumb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if crop_path and os.path.exists(crop_path):
                pix = QPixmap(crop_path)
                if not pix.isNull():
                    thumb_item.setIcon(QIcon(create_rounded_thumb(pix, 42)))
                else:
                    thumb_item.setIcon(QIcon(create_placeholder_thumb(42)))
            else:
                thumb_item.setIcon(QIcon(create_placeholder_thumb(42)))
            thumb_item.setData(Qt.ItemDataRole.UserRole, crop_path)
            self.table.setItem(row_idx, 0, thumb_item)

            # 2. Timestamp
            ts_str = log.get("timestamp") or ""
            ts_item = QTableWidgetItem(ts_str)
            ts_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            ts_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(row_idx, 1, ts_item)

            # 3. Name
            name_str = log.get("user_name") or i18n.t("hud_unknown")
            name_item = QTableWidgetItem(name_str)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            self.table.setItem(row_idx, 2, name_item)

            # 4. Direction Badge
            direction = (log.get("direction") or "").upper()
            dir_label = i18n.translate_direction(direction)
            dir_widget = QWidget()
            dir_layout = QHBoxLayout(dir_widget)
            dir_layout.setContentsMargins(6, 8, 6, 8)
            dir_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            badge = QLabel(f" {dir_label} ")
            if direction == "ENTER":
                badge.setStyleSheet(
                    "background-color: #064E3B; color: #34D399; font-weight: bold; "
                    "font-size: 11px; border-radius: 4px; padding: 2px 6px;"
                )
            else:
                badge.setStyleSheet(
                    "background-color: #7C2D12; color: #FDBA74; font-weight: bold; "
                    "font-size: 11px; border-radius: 4px; padding: 2px 6px;"
                )
            dir_layout.addWidget(badge)
            self.table.setCellWidget(row_idx, 3, dir_widget)

            # 5. Emotion
            emotion_raw = log.get("emotion") or "Neutral"
            emotion_label = i18n.translate_emotion(emotion_raw)
            emo_item = QTableWidgetItem(emotion_label)
            emo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            emo_item.setForeground(QColor("#CBD5E1"))
            self.table.setItem(row_idx, 4, emo_item)

            # 6. Actions (Delete button)
            log_id = log.get("id")
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 6, 4, 6)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_del = QPushButton(i18n.t("btn_delete_record"))
            btn_del.setFixedHeight(28)
            btn_del.setFixedWidth(64)
            btn_del.setStyleSheet(
                "QPushButton { background-color: #450A0A; color: #FCA5A5; border: 1px solid #7F1D1D; "
                "border-radius: 4px; font-size: 11px; font-weight: bold; } "
                "QPushButton:hover { background-color: #7F1D1D; color: #FFFFFF; }"
            )
            btn_del.clicked.connect(lambda _, lid=log_id, nm=name_str, tst=ts_str: self._delete_record(lid, nm, tst))
            action_layout.addWidget(btn_del)
            self.table.setCellWidget(row_idx, 5, action_widget)

    # ── Interactive Handlers ─────────────────────────────────────────────────

    def _on_table_double_clicked(self, row: int, col: int):
        """Open high-res image preview on row or thumbnail double-click."""
        if 0 <= row < len(self._current_logs):
            log = self._current_logs[row]
            crop_path = log.get("crop_path") or ""
            name = log.get("user_name") or i18n.t("hud_unknown")
            ts = log.get("timestamp") or ""
            dir_str = i18n.translate_direction(log.get("direction") or "")
            emo_str = i18n.translate_emotion(log.get("emotion") or "Neutral")

            details = f"{name} • {dir_str} • {emo_str}\n{ts}"
            title = i18n.t("image_preview_title", name=name)

            if crop_path and os.path.exists(crop_path):
                dialog = ImagePreviewDialog(crop_path, title=title, details=details, parent=self)
                dialog.exec()

    def _delete_record(self, log_id: int, name: str, timestamp: str):
        """Confirm and permanently delete a facial event log."""
        reply = QMessageBox.question(
            self,
            i18n.t("confirm_delete_record_title"),
            i18n.t("confirm_delete_record_msg", name=name, time=timestamp),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                database.delete_log(log_id)
                self._refresh_stats()
                self._load_logs()
            except Exception as exc:
                logger.error("Failed to delete log %d: %s", log_id, exc)
                QMessageBox.critical(self, i18n.t("error_deleting_title"), str(exc))

    def _export_csv(self):
        """Export all logs to a CSV file."""
        default_filename = f"{i18n.t('csv_default_name')}_historico.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.t("menu_export_csv"),
            default_filename,
            i18n.t("csv_filter"),
        )
        if path:
            try:
                count = database.export_logs_csv(path)
                QMessageBox.information(
                    self,
                    i18n.t("export_complete_title"),
                    i18n.t("export_complete_msg", count=count, path=path),
                )
            except Exception as exc:
                logger.error("Export logs CSV failed: %s", exc)
                QMessageBox.critical(self, i18n.t("error_saving_title"), str(exc))
