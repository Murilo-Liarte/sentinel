"""
user_manager_dialog.py — Sentinel User Management Center & Database
===================================================================
Provides a comprehensive, theme-aware user database management interface:
  - Asynchronous background photo enrollment with dlib mutex locking and image downscaling.
  - Dedicated User Manager dialog with multi-field search, role/status filtering, and live statistics.
  - Detailed profile editing: Name, Role, Document/Apt, Phone/WhatsApp, Email, Status, Notes.
  - File photo registration (auto face detection & avatar cropping) + live camera capture.
  - Full CSV export and safe deletion.
"""

import os
import time
import uuid
import logging
from typing import Optional, Dict, Any, List

import cv2
import numpy as np

from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QImage, QPixmap, QIcon, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTextEdit, QFileDialog, QMessageBox, QFrame,
    QProgressBar, QWidget, QAbstractItemView, QMenu
)

import i18n
import database
from app_paths import get_avatars_dir, get_resource
from camera_worker import _DLIB_LOCK, FACE_RECOGNITION_AVAILABLE

if FACE_RECOGNITION_AVAILABLE:
    import face_recognition as _fr
else:
    _fr = None

logger = logging.getLogger("Sentinel.UserManager")


# ── Helpers for Avatar Rendering ──────────────────────────────────────────────

def create_rounded_pixmap(pixmap: QPixmap, size: int = 42) -> QPixmap:
    """Create a circular/rounded avatar pixmap for table cells and previews."""
    scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, size // 2, size // 2)
    painter.setClipPath(path)

    # Center crop if aspect ratio differs
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()

    return result


def create_placeholder_avatar(size: int = 42, letter: str = "?") -> QPixmap:
    """Generate a clean letter avatar when no face image exists."""
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, size // 2, size // 2)
    painter.setClipPath(path)

    painter.fillRect(0, 0, size, size, Qt.GlobalColor.darkGray)
    painter.setPen(Qt.GlobalColor.white)
    font = painter.font()
    font.setPixelSize(size // 2)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, letter.upper()[:1])
    painter.end()

    return result


# ── Background Worker for Photo Enrollment ───────────────────────────────────

class PhotoEnrollmentWorker(QThread):
    """
    Background worker thread to decode images, detect faces via dlib,
    extract 128-d embeddings, and generate cropped portrait avatars.
    Guarantees thread-safety with _DLIB_LOCK and never blocks the GUI.
    """
    success = Signal(object, str, object)   # (embedding: np.ndarray, avatar_path: str, qimage: QImage)
    failure = Signal(str)                   # error_message
    status_update = Signal(str)

    def __init__(self, filepath: Optional[str] = None, frame_np: Optional[np.ndarray] = None, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.frame_np = frame_np

    def run(self):
        try:
            self.status_update.emit(i18n.t("enroll_status_processing"))

            # 1. Load image
            if self.filepath:
                if not os.path.exists(self.filepath):
                    self.failure.emit(i18n.t("enroll_err_file_not_found"))
                    return
                # Use OpenCV to read image, supporting unicode paths on Windows
                img_data = np.fromfile(self.filepath, dtype=np.uint8)
                bgr = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                if bgr is None:
                    self.failure.emit(i18n.t("enroll_err_invalid_image"))
                    return
            elif self.frame_np is not None:
                bgr = self.frame_np.copy()
            else:
                self.failure.emit(i18n.t("enroll_err_no_input"))
                return

            h, w = bgr.shape[:2]

            # 2. Rescale large images (> 1080p) to avoid high memory spikes
            max_dim = max(h, w)
            if max_dim > 1920:
                scale = 1920.0 / max_dim
                bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                h, w = bgr.shape[:2]

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

            if not FACE_RECOGNITION_AVAILABLE or _fr is None:
                self.failure.emit(i18n.t("enroll_err_dlib_unavailable"))
                return

            # 3. Detect faces with thread-safe dlib mutex
            self.status_update.emit(i18n.t("enroll_status_detecting"))
            with _DLIB_LOCK:
                locs = _fr.face_locations(rgb, model="hog")
                if not locs:
                    self.failure.emit(i18n.t("enroll_err_no_face"))
                    return

                # If multiple faces detected, pick the largest (closest/most prominent)
                if len(locs) > 1:
                    def _box_area(box):
                        top, right, bottom, left = box
                        return (bottom - top) * (right - left)
                    locs.sort(key=_box_area, reverse=True)

                chosen_loc = locs[0]
                encs = _fr.face_encodings(rgb, [chosen_loc])

            if not encs:
                self.failure.emit(i18n.t("enroll_err_encoding_failed"))
                return

            raw_emb = encs[0].astype(np.float32)
            norm = np.linalg.norm(raw_emb)
            embedding = raw_emb if norm == 0 else (raw_emb / norm)

            # 4. Crop face with 20% portrait margin for avatar
            top, right, bottom, left = chosen_loc
            fh, fw = bottom - top, right - left
            margin_y = int(fh * 0.25)
            margin_x = int(fw * 0.20)

            c_top = max(0, top - margin_y)
            c_bottom = min(h, bottom + margin_y)
            c_left = max(0, left - margin_x)
            c_right = min(w, right + margin_x)

            face_crop = bgr[c_top:c_bottom, c_left:c_right]

            # 5. Save avatar JPEG to persistent directory
            avatars_dir = get_avatars_dir()
            filename = f"avatar_{uuid.uuid4().hex[:12]}.jpg"
            avatar_path = os.path.join(avatars_dir, filename)

            # Resize avatar to standard 160x160 for crisp high-DPI display
            avatar_resized = cv2.resize(face_crop, (160, 160), interpolation=cv2.INTER_LANCZOS4)
            cv2.imwrite(avatar_path, avatar_resized, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # Convert to QImage for preview
            rgb_crop = cv2.cvtColor(avatar_resized, cv2.COLOR_BGR2RGB)
            ch = 3
            qimg = QImage(rgb_crop.data, 160, 160, ch * 160, QImage.Format.Format_RGB888).copy()

            self.success.emit(embedding, avatar_path, qimg)

        except Exception as exc:
            logger.exception("PhotoEnrollmentWorker failed: %s", exc)
            self.failure.emit(str(exc))


# ── Add / Edit User Dialog ───────────────────────────────────────────────────

class UserEditDialog(QDialog):
    """
    Detailed modal dialog for creating a new user or editing an existing user.
    Supports camera freeze snapshot or photo file upload.
    """
    user_saved = Signal(int)

    def __init__(self, user_id: Optional[int] = None, parent=None, camera_worker=None):
        super().__init__(parent)
        self.user_id = user_id
        self.camera_worker = camera_worker
        self.is_edit = user_id is not None

        self._pending_embedding: Optional[np.ndarray] = None
        self._avatar_path: str = ""
        self._enrollment_worker: Optional[PhotoEnrollmentWorker] = None

        title_key = "user_dialog_edit_title" if self.is_edit else "user_dialog_create_title"
        self.setWindowTitle(i18n.t(title_key))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(500, 520)
        self.resize(560, 580)

        icon_path = get_resource("sentinel.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        if self.is_edit:
            self._load_existing_user()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Title
        title_label = QLabel(i18n.t("user_dialog_edit_title" if self.is_edit else "user_dialog_create_title"))
        title_label.setObjectName("section_title")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title_label)

        # Main two-column row
        content_row = QHBoxLayout()
        content_row.setSpacing(18)

        # Left column: Avatar preview and enrollment controls
        avatar_col = QVBoxLayout()
        avatar_col.setSpacing(8)
        avatar_col.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.avatar_preview = QLabel()
        self.avatar_preview.setFixedSize(140, 140)
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_preview.setStyleSheet(
            "border: 2px dashed #475569; border-radius: 70px; background-color: #0F172A;"
        )
        self.avatar_preview.setPixmap(create_placeholder_avatar(136, "?"))
        avatar_col.addWidget(self.avatar_preview)

        # Status text below avatar
        self.avatar_status = QLabel(i18n.t("user_avatar_hint"))
        self.avatar_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_status.setWordWrap(True)
        self.avatar_status.setStyleSheet("color: #94A3B8; font-size: 11px;")
        avatar_col.addWidget(self.avatar_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        avatar_col.addWidget(self.progress_bar)

        # Upload photo button
        self.btn_upload_photo = QPushButton(i18n.t("btn_upload_photo"))
        self.btn_upload_photo.setFixedHeight(30)
        self.btn_upload_photo.clicked.connect(self._on_upload_photo)
        avatar_col.addWidget(self.btn_upload_photo)

        # Capture from camera button
        self.btn_cam_capture = QPushButton(i18n.t("btn_cam_capture"))
        self.btn_cam_capture.setFixedHeight(30)
        self.btn_cam_capture.clicked.connect(self._on_cam_capture)
        avatar_col.addWidget(self.btn_cam_capture)

        content_row.addLayout(avatar_col, stretch=1)

        # Right column: Form fields
        form_col = QVBoxLayout()
        form_col.setSpacing(8)

        # Name field
        lbl_name = QLabel(i18n.t("name_label"))
        lbl_name.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(i18n.t("name_placeholder"))
        self.input_name.setFixedHeight(30)
        form_col.addWidget(lbl_name)
        form_col.addWidget(self.input_name)

        # Role and Status row
        role_status_row = QHBoxLayout()
        role_box = QVBoxLayout()
        lbl_role = QLabel(i18n.t("role_label"))
        lbl_role.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.combo_role = QComboBox()
        self.combo_role.setFixedHeight(30)
        self.combo_role.addItems(i18n.get_roles_list())
        role_box.addWidget(lbl_role)
        role_box.addWidget(self.combo_role)
        role_status_row.addLayout(role_box, 1)

        status_box = QVBoxLayout()
        lbl_status = QLabel(i18n.t("user_status_label"))
        lbl_status.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(30)
        self.combo_status.addItem(f"🟢 {i18n.t('status_active')}", "active")
        self.combo_status.addItem(f"⏸️ {i18n.t('status_inactive')}", "inactive")
        self.combo_status.addItem(f"🚫 {i18n.t('status_blocked')}", "blocked")
        status_box.addWidget(lbl_status)
        status_box.addWidget(self.combo_status)
        role_status_row.addLayout(status_box, 1)

        form_col.addLayout(role_status_row)

        # Document / Apt / Badge
        lbl_doc = QLabel(i18n.t("user_doc_label"))
        lbl_doc.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.input_doc = QLineEdit()
        self.input_doc.setPlaceholderText(i18n.t("user_doc_placeholder"))
        self.input_doc.setFixedHeight(30)
        form_col.addWidget(lbl_doc)
        form_col.addWidget(self.input_doc)

        # Phone / WhatsApp
        lbl_phone = QLabel(i18n.t("user_phone_label"))
        lbl_phone.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText(i18n.t("user_phone_placeholder"))
        self.input_phone.setFixedHeight(30)
        form_col.addWidget(lbl_phone)
        form_col.addWidget(self.input_phone)

        # Email
        lbl_email = QLabel(i18n.t("user_email_label"))
        lbl_email.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText(i18n.t("user_email_placeholder"))
        self.input_email.setFixedHeight(30)
        form_col.addWidget(lbl_email)
        form_col.addWidget(self.input_email)

        # Notes / Observations
        lbl_notes = QLabel(i18n.t("user_notes_label"))
        lbl_notes.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.input_notes = QTextEdit()
        self.input_notes.setPlaceholderText(i18n.t("user_notes_placeholder"))
        self.input_notes.setFixedHeight(60)
        form_col.addWidget(lbl_notes)
        form_col.addWidget(self.input_notes)

        content_row.addLayout(form_col, stretch=2)
        layout.addLayout(content_row)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton(i18n.t("cancel"))
        self.btn_cancel.setFixedHeight(32)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton(i18n.t("btn_save"))
        self.btn_save.setObjectName("btnStart")
        self.btn_save.setFixedHeight(32)
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def _load_existing_user(self):
        user = database.get_user_by_id(self.user_id)
        if not user:
            return

        self.input_name.setText(user["name"])
        idx = self.combo_role.findText(user["role"])
        if idx >= 0:
            self.combo_role.setCurrentIndex(idx)

        st_idx = self.combo_status.findData(user["status"])
        if st_idx >= 0:
            self.combo_status.setCurrentIndex(st_idx)

        self.input_doc.setText(user["doc_id"])
        self.input_phone.setText(user["phone"])
        self.input_email.setText(user["email"])
        self.input_notes.setPlainText(user["notes"])

        if user["avatar_path"] and os.path.exists(user["avatar_path"]):
            self._avatar_path = user["avatar_path"]
            pix = QPixmap(self._avatar_path)
            if not pix.isNull():
                self.avatar_preview.setPixmap(create_rounded_pixmap(pix, 136))
                self.avatar_status.setText(i18n.t("user_avatar_saved"))

    def _on_upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            i18n.t("select_photo_title"),
            "",
            "Imagens (*.jpg *.jpeg *.png *.bmp *.webp);;Todos os Arquivos (*.*)"
        )
        if not file_path:
            return

        self._start_enrollment(filepath=file_path)

    def _on_cam_capture(self):
        if not self.camera_worker or not self.camera_worker.isRunning():
            QMessageBox.warning(
                self,
                i18n.t("alert_cam_not_running_title"),
                i18n.t("alert_cam_not_running_msg")
            )
            return

        # Connect to one-shot capture signal
        self.camera_worker.capture_done.connect(self._on_camera_capture_done)
        self.camera_worker.request_capture()
        self.avatar_status.setText(i18n.t("status_capturing"))
        self.progress_bar.setVisible(True)

    def _on_camera_capture_done(self, embedding, q_img):
        try:
            self.camera_worker.capture_done.disconnect(self._on_camera_capture_done)
        except Exception:
            pass

        self.progress_bar.setVisible(False)
        if embedding is not None and q_img is not None:
            self._pending_embedding = embedding

            # Save snapshot to avatar file
            pix = QPixmap.fromImage(q_img)
            avatars_dir = get_avatars_dir()
            filename = f"avatar_{uuid.uuid4().hex[:12]}.jpg"
            avatar_path = os.path.join(avatars_dir, filename)
            pix.save(avatar_path, "JPG", 95)
            self._avatar_path = avatar_path

            self.avatar_preview.setPixmap(create_rounded_pixmap(pix, 136))
            self.avatar_status.setText(i18n.t("status_captured_success"))
        else:
            self.avatar_status.setText(i18n.t("status_no_face_detected"))
            QMessageBox.warning(
                self,
                i18n.t("alert_no_face_title"),
                i18n.t("alert_no_face_msg")
            )

    def _start_enrollment(self, filepath: Optional[str] = None, frame_np: Optional[np.ndarray] = None):
        self.progress_bar.setVisible(True)
        self.btn_upload_photo.setEnabled(False)
        self.btn_cam_capture.setEnabled(False)

        self._enrollment_worker = PhotoEnrollmentWorker(filepath=filepath, frame_np=frame_np, parent=self)
        self._enrollment_worker.status_update.connect(lambda msg: self.avatar_status.setText(msg))
        self._enrollment_worker.success.connect(self._on_enrollment_success)
        self._enrollment_worker.failure.connect(self._on_enrollment_failure)
        self._enrollment_worker.start()

    def _on_enrollment_success(self, embedding: np.ndarray, avatar_path: str, qimg: QImage):
        self.progress_bar.setVisible(False)
        self.btn_upload_photo.setEnabled(True)
        self.btn_cam_capture.setEnabled(True)

        self._pending_embedding = embedding
        self._avatar_path = avatar_path

        pix = QPixmap.fromImage(qimg)
        self.avatar_preview.setPixmap(create_rounded_pixmap(pix, 136))
        self.avatar_status.setText(i18n.t("status_captured_success"))

    def _on_enrollment_failure(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_upload_photo.setEnabled(True)
        self.btn_cam_capture.setEnabled(True)

        self.avatar_status.setText(error_msg)
        QMessageBox.warning(self, i18n.t("alert_no_face_title"), error_msg)

    def _on_save_clicked(self):
        name = self.input_name.text().strip()
        role = self.combo_role.currentText()
        status = self.combo_status.currentData() or "active"
        doc_id = self.input_doc.text().strip()
        phone = self.input_phone.text().strip()
        email = self.input_email.text().strip()
        notes = self.input_notes.toPlainText().strip()

        if not name:
            QMessageBox.warning(
                self,
                i18n.t("alert_name_required_title"),
                i18n.t("alert_name_required_msg")
            )
            return

        if not self.is_edit and self._pending_embedding is None:
            QMessageBox.warning(
                self,
                i18n.t("alert_no_face_title"),
                i18n.t("alert_no_face_msg")
            )
            return

        try:
            if self.is_edit:
                database.update_user(
                    user_id=self.user_id,
                    name=name,
                    role=role,
                    phone=phone,
                    email=email,
                    doc_id=doc_id,
                    notes=notes,
                    status=status,
                    avatar_path=self._avatar_path if self._avatar_path else None,
                    embedding=self._pending_embedding,
                )
                saved_id = self.user_id
            else:
                saved_id = database.add_user(
                    name=name,
                    role=role,
                    embedding=self._pending_embedding,
                    phone=phone,
                    email=email,
                    doc_id=doc_id,
                    notes=notes,
                    status=status,
                    avatar_path=self._avatar_path,
                )

            # Reload vectorized matrix in camera worker if running
            if self.camera_worker:
                self.camera_worker.reload_embeddings()

            self.user_saved.emit(saved_id)
            self.accept()

        except Exception as exc:
            logger.exception("Failed to save user: %s", exc)
            QMessageBox.critical(
                self,
                i18n.t("error_saving_title"),
                i18n.t("error_saving_msg", error=str(exc))
            )


# ── Full User Management Dialog ──────────────────────────────────────────────

class UserManagerDialog(QDialog):
    """
    Consumer-grade, full-featured User Management Center:
      - Real-time search across names, documents, phones, emails.
      - Role and Status filtering.
      - Statistics cards.
      - Table with face avatars, badges, and inline actions.
      - CSV export and profile modification.
    """
    database_changed = Signal()

    def __init__(self, camera_worker=None, parent=None):
        super().__init__(parent)
        self.camera_worker = camera_worker

        self.setWindowTitle(i18n.t("user_mgr_title"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(780, 480)
        self.resize(920, 600)

        icon_path = get_resource("sentinel.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self._refresh_table()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        # ── Header & Stats Bar ───────────────────────────────────────────────
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel(i18n.t("user_mgr_title"))
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        subtitle_lbl = QLabel(i18n.t("user_mgr_subtitle"))
        subtitle_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Stats Badges
        self.stat_total_badge = QLabel("0")
        self.stat_total_badge.setStyleSheet(
            "background-color: #1E293B; color: #38BDF8; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
        )
        self.stat_active_badge = QLabel("0")
        self.stat_active_badge.setStyleSheet(
            "background-color: #052E16; color: #4ADE80; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
        )
        self.stat_inactive_badge = QLabel("0")
        self.stat_inactive_badge.setStyleSheet(
            "background-color: #451A03; color: #FDBA74; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
        )
        self.stat_blocked_badge = QLabel("0")
        self.stat_blocked_badge.setStyleSheet(
            "background-color: #450A0A; color: #F87171; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 12px;"
        )

        header_row.addWidget(self.stat_total_badge)
        header_row.addWidget(self.stat_active_badge)
        header_row.addWidget(self.stat_inactive_badge)
        header_row.addWidget(self.stat_blocked_badge)
        root_layout.addLayout(header_row)

        # ── Toolbar: Search, Filters, Add Button, Export Button ──────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(i18n.t("user_search_placeholder"))
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._refresh_table)
        toolbar.addWidget(self.search_input, stretch=3)

        # Role Filter
        self.role_filter = QComboBox()
        self.role_filter.setFixedHeight(32)
        self.role_filter.addItem(i18n.t("filter_all_roles"), "all")
        for r in i18n.get_roles_list():
            self.role_filter.addItem(r, r)
        self.role_filter.currentIndexChanged.connect(self._refresh_table)
        toolbar.addWidget(self.role_filter, stretch=1)

        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(32)
        self.status_filter.addItem(i18n.t("filter_all_statuses"), "all")
        self.status_filter.addItem(f"🟢 {i18n.t('filter_status_active')}", "active")
        self.status_filter.addItem(f"⏸️ {i18n.t('filter_status_inactive')}", "inactive")
        self.status_filter.addItem(f"🚫 {i18n.t('filter_status_blocked')}", "blocked")
        self.status_filter.currentIndexChanged.connect(self._refresh_table)
        toolbar.addWidget(self.status_filter, stretch=1)

        # Export CSV Button
        self.btn_export = QPushButton(i18n.t("btn_export_users"))
        self.btn_export.setFixedHeight(32)
        self.btn_export.clicked.connect(self._on_export_csv)
        toolbar.addWidget(self.btn_export)

        # New User Button
        self.btn_new_user = QPushButton(i18n.t("btn_new_user"))
        self.btn_new_user.setObjectName("btnStart")
        self.btn_new_user.setFixedHeight(32)
        self.btn_new_user.clicked.connect(self._on_new_user_clicked)
        toolbar.addWidget(self.btn_new_user)

        root_layout.addLayout(toolbar)

        # ── Main User Table ──────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            i18n.t("col_avatar"),
            i18n.t("col_name"),
            i18n.t("col_role"),
            i18n.t("col_doc"),
            i18n.t("col_contact"),
            i18n.t("col_status"),
            i18n.t("col_registered_at"),
            i18n.t("col_actions"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setIconSize(QSize(40, 40))

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(7, 185)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        root_layout.addWidget(self.table, stretch=1)

        # ── Bottom row with close button ─────────────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        self.btn_close = QPushButton(i18n.t("close"))
        self.btn_close.setFixedHeight(30)
        self.btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_close)
        root_layout.addLayout(bottom_row)

    def _refresh_table(self):
        query = self.search_input.text().strip()
        role = self.role_filter.currentData() or "all"
        status = self.status_filter.currentData() or "all"

        # Update stats
        stats = database.get_user_stats()
        self.stat_total_badge.setText(f"{i18n.t('stat_total')}: {stats['total']}")
        self.stat_active_badge.setText(f"{i18n.t('stat_active')}: {stats['active']}")
        self.stat_inactive_badge.setText(f"{i18n.t('stat_inactive')}: {stats.get('inactive', 0)}")
        self.stat_blocked_badge.setText(f"{i18n.t('stat_blocked')}: {stats.get('blocked', 0)}")

        users = database.get_users_detailed(query=query, role=role, status=status, limit=300)

        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 48)

            uid = u["id"]
            name = u["name"]

            # 0. Avatar
            avatar_lbl = QLabel()
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if u["avatar_path"] and os.path.exists(u["avatar_path"]):
                pix = QPixmap(u["avatar_path"])
                if not pix.isNull():
                    avatar_lbl.setPixmap(create_rounded_pixmap(pix, 36))
                else:
                    avatar_lbl.setPixmap(create_placeholder_avatar(36, name))
            else:
                avatar_lbl.setPixmap(create_placeholder_avatar(36, name))
            self.table.setCellWidget(row, 0, avatar_lbl)

            # 1. Name
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, uid)
            self.table.setItem(row, 1, item_name)

            # 2. Role (styled badge)
            role_item = QTableWidgetItem(u["role"])
            self.table.setItem(row, 2, role_item)

            # 3. Document / Apt
            self.table.setItem(row, 3, QTableWidgetItem(u["doc_id"] or "-"))

            # 4. Contact
            contact_str = u["phone"] or u["email"] or "-"
            self.table.setItem(row, 4, QTableWidgetItem(contact_str))

            # 5. Status Badge
            u_status = u["status"] or "active"
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            badge = QLabel()
            if u_status == "active":
                badge.setText(f" 🟢 {i18n.t('status_active')} ")
                badge.setStyleSheet(
                    "background-color: #052E16; color: #4ADE80; font-weight: bold; "
                    "border-radius: 4px; padding: 2px 6px; font-size: 11px;"
                )
            elif u_status == "inactive":
                badge.setText(f" ⏸️ {i18n.t('status_inactive')} ")
                badge.setStyleSheet(
                    "background-color: #451A03; color: #FDBA74; font-weight: bold; "
                    "border-radius: 4px; padding: 2px 6px; font-size: 11px;"
                )
            else:  # blocked
                badge.setText(f" 🚫 {i18n.t('status_blocked')} ")
                badge.setStyleSheet(
                    "background-color: #450A0A; color: #F87171; font-weight: bold; "
                    "border-radius: 4px; padding: 2px 6px; font-size: 11px;"
                )
            status_layout.addWidget(badge)
            self.table.setCellWidget(row, 5, status_widget)

            # 6. Registered At
            reg_display = u["registered_at"][:16] if len(u["registered_at"]) >= 16 else u["registered_at"]
            self.table.setItem(row, 6, QTableWidgetItem(reg_display))

            # 7. Action buttons (Status, Edit & Delete)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            btn_status = QPushButton(f"⚡ {i18n.t('btn_quick_status')}")
            btn_status.setFixedHeight(26)
            btn_status.setStyleSheet(
                "QPushButton { background-color: #1E293B; border: 1px solid #334155; "
                "border-radius: 4px; font-size: 11px; padding: 0 6px; font-weight: bold; } "
                "QPushButton:hover { background-color: #334155; }"
            )
            btn_status.clicked.connect(
                lambda _, b=btn_status, user_id=uid, user_name=name: self._show_quick_status_menu(b, user_id, user_name)
            )

            btn_edit = QPushButton(i18n.t("btn_edit"))
            btn_edit.setFixedHeight(26)
            btn_edit.clicked.connect(lambda checked, user_id=uid: self._on_edit_user(user_id))

            btn_del = QPushButton("X")
            btn_del.setObjectName("btn_icon")
            btn_del.setFixedSize(26, 26)
            btn_del.setToolTip(i18n.t("btn_delete_tooltip", name=name))
            btn_del.clicked.connect(lambda checked, user_id=uid, user_name=name: self._on_delete_user(user_id, user_name))

            actions_layout.addWidget(btn_status)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            self.table.setCellWidget(row, 7, actions_widget)

    def _show_quick_status_menu(self, button: QPushButton, user_id: int, user_name: str):
        """Open quick status toggle menu below the status button."""
        menu = QMenu(self)
        act_active = menu.addAction(f"🟢 {i18n.t('action_set_active')}")
        act_active.triggered.connect(lambda: self._on_change_user_status(user_id, "active", user_name))

        act_inactive = menu.addAction(f"⏸️ {i18n.t('action_set_inactive')}")
        act_inactive.triggered.connect(lambda: self._on_change_user_status(user_id, "inactive", user_name))

        act_blocked = menu.addAction(f"🚫 {i18n.t('action_set_blocked')}")
        act_blocked.triggered.connect(lambda: self._on_change_user_status(user_id, "blocked", user_name))

        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _on_table_context_menu(self, pos):
        """Open context menu with status change and profile actions on right-click."""
        index = self.table.indexAt(pos)
        row = index.row()
        if row < 0:
            return

        name_item = self.table.item(row, 1)
        if not name_item:
            return
        uid = name_item.data(Qt.ItemDataRole.UserRole)
        name = name_item.text()

        menu = QMenu(self)
        menu.addAction(f"🟢 {i18n.t('action_set_active')}", lambda: self._on_change_user_status(uid, "active", name))
        menu.addAction(f"⏸️ {i18n.t('action_set_inactive')}", lambda: self._on_change_user_status(uid, "inactive", name))
        menu.addAction(f"🚫 {i18n.t('action_set_blocked')}", lambda: self._on_change_user_status(uid, "blocked", name))
        menu.addSeparator()
        menu.addAction(f"✏️ {i18n.t('btn_edit')}", lambda: self._on_edit_user(uid))
        menu.addAction(f"🗑️ {i18n.t('btn_delete') if i18n.t('btn_delete') else 'Excluir'}", lambda: self._on_delete_user(uid, name))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_change_user_status(self, user_id: int, new_status: str, user_name: str):
        """Update access status directly from table action or context menu."""
        try:
            database.set_user_status(user_id, new_status)
            if self.camera_worker:
                self.camera_worker.reload_embeddings()
            self._refresh_table()
            self.database_changed.emit()
        except Exception as exc:
            logger.exception("Failed to change user status: %s", exc)
            QMessageBox.critical(self, i18n.t("error_saving_title"), str(exc))

    def _on_cell_double_clicked(self, row: int, col: int):
        name_item = self.table.item(row, 1)
        if name_item:
            user_id = name_item.data(Qt.ItemDataRole.UserRole)
            if user_id:
                self._on_edit_user(user_id)

    def _on_new_user_clicked(self):
        dlg = UserEditDialog(parent=self, camera_worker=self.camera_worker)
        dlg.user_saved.connect(self._on_user_saved)
        dlg.exec()

    def _on_edit_user(self, user_id: int):
        dlg = UserEditDialog(user_id=user_id, parent=self, camera_worker=self.camera_worker)
        dlg.user_saved.connect(self._on_user_saved)
        dlg.exec()

    def _on_user_saved(self, user_id: int):
        self._refresh_table()
        self.database_changed.emit()

    def _on_delete_user(self, user_id: int, user_name: str):
        reply = QMessageBox.question(
            self,
            i18n.t("confirm_unregister_title"),
            i18n.t("confirm_unregister_msg", name=user_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            database.delete_user(user_id)
            if self.camera_worker:
                self.camera_worker.reload_embeddings()
            self._refresh_table()
            self.database_changed.emit()

    def _on_export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.t("export_complete_title"),
            "usuarios_sentinel.csv",
            i18n.t("csv_filter")
        )
        if not file_path:
            return

        try:
            count = database.export_users_csv(file_path)
            QMessageBox.information(
                self,
                i18n.t("export_complete_title"),
                i18n.t("export_complete_msg", count=count, path=file_path)
            )
        except Exception as exc:
            logger.exception("Failed to export users CSV: %s", exc)
            QMessageBox.critical(
                self,
                i18n.t("error_saving_title"),
                str(exc)
            )
