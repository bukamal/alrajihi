# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QMessageBox, QHBoxLayout, QApplication, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from auth.activation import activate
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from i18n import translate


class ActivationThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, key):
        super().__init__()
        self.key = key

    def run(self):
        try:
            self.progress.emit(20, translate('phase233_ui_118'))
            self.progress.emit(45, translate('phase233_ui_119'))
            success, msg = activate(self.key)
            if success:
                self.progress.emit(100, translate('phase233_ui_116'))
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, msg or translate('phase233_ui_117'))
        except Exception as e:
            self.finished.emit(False, str(e))


class ActivationDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('phase233_ui_006'))
        self.resize(520, 460)
        self.setMinimumSize(460, 420)

        self.main_frame.setObjectName('activationCard')
        self.main_frame.setStyleSheet(ThemeManager.get_stylesheet())
        try:
            DesignSystem.apply_shadow(self.main_frame, blur=30, y=10, alpha=70)
        except Exception:
            pass

        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(18)
        layout.setContentsMargins(34, 28, 34, 30)

        logo = QLabel("🔐")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 48px;")
        layout.addWidget(logo)

        title = QLabel(translate('phase233_ui_007'))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ThemeManager.get('primary')};")
        layout.addWidget(title)

        desc = QLabel(translate('phase233_ui_008'))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {ThemeManager.get('text_secondary')};")
        layout.addWidget(desc)

        activation_mode_hint = DesignSystem.status_pill(translate('phase233_ui_120'), "info")
        layout.addWidget(activation_mode_hint)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(translate('phase233_ui_121'))
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.returnPressed.connect(self._activate)
        layout.addWidget(self.key_edit)

        self.show_key = QCheckBox(translate('phase233_ui_009'))
        self.show_key.toggled.connect(lambda checked: self.key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        layout.addWidget(self.show_key)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status_label = QLabel(translate('phase233_ui_010'))
        self.status_label.setStyleSheet(f"color: {ThemeManager.get('text_muted')}; font-size: 12px;")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        self.activate_btn = DesignSystem.primary_button(translate('phase233_ui_122'))
        self.activate_btn.setObjectName("primary")
        self.activate_btn.setIcon(qta.icon('fa5s.check'))
        self.activate_btn.clicked.connect(self._activate)

        self.retry_btn = DesignSystem.secondary_button("إعادة المحاولة")
        self.retry_btn.setIcon(qta.icon('fa5s.redo'))
        self.retry_btn.setEnabled(False)
        self.retry_btn.clicked.connect(self._activate)

        cancel_btn = DesignSystem.secondary_button(translate('phase233_ui_020'))
        cancel_btn.setIcon(qta.icon('fa5s.times'))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.activate_btn)
        btn_layout.addWidget(self.retry_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.fade_in()

    def _set_status(self, text, color_key='text_muted'):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {ThemeManager.get(color_key)}; font-size: 12px;")

    def _activate(self):
        key = self.key_edit.text().strip()
        if not key:
            self._set_status("يرجى إدخال مفتاح الترخيص", 'danger')
            self.key_edit.setFocus()
            return
        self.activate_btn.setEnabled(False)
        self.retry_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(5)
        self._set_status("جاري بدء التفعيل...", 'info')
        self.thread = ActivationThread(key)
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_finished)
        self.thread.start()

    def _on_progress(self, value, message):
        self.progress.setValue(max(0, min(100, value)))
        self._set_status(message, 'info')
        QApplication.processEvents()

    def _on_finished(self, success, msg):
        self.activate_btn.setEnabled(True)
        self.retry_btn.setEnabled(not success)
        if success:
            self.progress.setValue(100)
            self._set_status("الترخيص صالح. تم التفعيل بنجاح.", 'success')
            QMessageBox.information(self, "نجاح", "تم التفعيل بنجاح. سيتم متابعة تشغيل التطبيق.")
            self.accept()
        else:
            self.progress.setVisible(False)
            hint = "تحقق من المفتاح أو اتصال الإنترنت ثم أعد المحاولة."
            self._set_status(f"فشل التفعيل: {msg}\n{hint}", 'danger')
