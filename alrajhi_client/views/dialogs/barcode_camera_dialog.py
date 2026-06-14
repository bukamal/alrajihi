# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from views.centered_dialog import CenteredDialog
from core.services.barcode_scanner_service import barcode_scanner_service
from utils import show_toast
from i18n import translate, qt_layout_direction
from core.services.settings_service import settings_service


class BarcodeCameraDialog(CenteredDialog):
    """Small camera scanner dialog for barcode/QR input.

    It is safe on systems without camera/OpenCV/pyzbar: the dialog shows a clear
    message and lets the user fall back to USB scanner/manual entry.
    """

    barcode_scanned = pyqtSignal(str, str)  # value, symbology

    def __init__(self, parent=None, camera_index: int = 0, auto_close: bool = True):
        super().__init__(parent)
        self.setWindowTitle(translate("barcode_camera_title"))
        self.resize(720, 560)
        self.setLayoutDirection(qt_layout_direction(settings_service.get_language()))
        self.camera_index = camera_index
        self.auto_close = auto_close
        self.capture = None
        self.last_value = None

        layout = QVBoxLayout(self.content_widget)
        self.status_label = QLabel(translate("ready"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.video_label = QLabel(translate("press_start_camera"))
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(360)
        self.video_label.setStyleSheet("border: 1px solid #aaa; background: #111; color: white;")
        layout.addWidget(self.video_label)

        controls = QHBoxLayout()
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2"])
        self.start_btn = QPushButton(translate("start_camera"))
        self.stop_btn = QPushButton(translate("stop"))
        self.close_btn = QPushButton(translate("close"))
        controls.addWidget(self.camera_combo)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.close_btn)
        layout.addLayout(controls)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_frame)
        self.start_btn.clicked.connect(self.start_camera)
        self.stop_btn.clicked.connect(self.stop_camera)
        self.close_btn.clicked.connect(self.reject)

        if not barcode_scanner_service.is_available():
            self.status_label.setText(
                translate("camera_unavailable_msg", reason=barcode_scanner_service.unavailable_reason())
            )
            self.start_btn.setEnabled(False)

    def start_camera(self):
        self.stop_camera()
        self.camera_index = self.camera_combo.currentIndex()
        self.capture = barcode_scanner_service.open_camera(self.camera_index)
        if not self.capture or not self.capture.isOpened():
            self.capture = None
            show_toast(translate("camera_open_failed_help"), "error", self)
            self.status_label.setText(translate("camera_open_failed"))
            return
        self.status_label.setText(translate("point_camera_to_barcode"))
        self.timer.start(80)

    def stop_camera(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.capture is not None:
            try:
                self.capture.release()
            except Exception:
                pass
            self.capture = None

    def _read_frame(self):
        if self.capture is None:
            return
        ok, frame = self.capture.read()
        if not ok or frame is None:
            return

        result = barcode_scanner_service.first_result(frame)
        if result and result.value != self.last_value:
            self.last_value = result.value
            self.status_label.setText(translate("barcode_detected", value=result.value, symbology=result.symbology))
            self.barcode_scanned.emit(result.value, result.symbology)
            if self.auto_close:
                self.accept()
                return

        cv2 = barcode_scanner_service.cv2
        if cv2 is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)

    def accept(self):
        self.stop_camera()
        super().accept()

    def reject(self):
        self.stop_camera()
        super().reject()
